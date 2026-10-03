// darkly-go: módulos rápidos de Darkly Tools (port scan + DNS).
// Salida siempre JSON por stdout. Sin dependencias externas, solo stdlib.
//
//	Uso:
//	  darkly-go scan --host 8.8.8.8 --ports 22,80,443 --timeout 1000 --workers 100
//	  darkly-go dns --host google.com
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"net"
	"net/http"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

var httpClient = &http.Client{Timeout: 12 * time.Second}

const goUA = "darkly-go/2.1 (educativo)"

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go <scan|dns> [flags]")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "scan":
		cmdScan(os.Args[2:])
	case "dns":
		cmdDNS(os.Args[2:])
	case "ping":
		cmdPing(os.Args[2:])
	case "subnet":
		cmdSubnet(os.Args[2:])
	case "traceroute":
		cmdTraceroute(os.Args[2:])
	case "hash":
		cmdHash(os.Args[2:])
	case "hashid":
		cmdHashID(os.Args[2:])
	case "pass":
		cmdPass(os.Args[2:])
	case "genpass":
		cmdGenPass(os.Args[2:])
	case "audit":
		cmdAudit(os.Args[2:])
	case "breach":
		cmdBreach(os.Args[2:])
	case "headers":
		cmdHeaders(os.Args[2:])
	case "urlscan":
		cmdURLScan(os.Args[2:])
	case "ipinfo":
		cmdIPInfo(os.Args[2:])
	case "ptr":
		cmdPTR(os.Args[2:])
	case "rdap":
		cmdRDAP(os.Args[2:])
	case "whois":
		cmdWhois(os.Args[2:])
	case "user":
		cmdUser(os.Args[2:])
	case "dnsrecords":
		cmdDNSRecords(os.Args[2:])
	case "subdomains":
		cmdSubdomains(os.Args[2:])
	case "ghuser":
		cmdGHUser(os.Args[2:])
	case "sysinfo":
		cmdSysInfo(os.Args[2:])
	case "filehash":
		cmdFileHash(os.Args[2:])
	case "verify":
		cmdVerify(os.Args[2:])
	case "report":
		cmdReport(os.Args[2:])
	case "menu":
		runMenu()
	case "version":
		fmt.Println("darkly-go v2.1.0")
	default:
		fmt.Fprintln(os.Stderr, "subcomando desconocido:", os.Args[1])
		os.Exit(2)
	}
}

// ---------- SCAN ----------

type portResult struct {
	Open   bool   `json:"open"`
	Banner string `json:"banner,omitempty"`
}

type scanOut struct {
	Host  string                `json:"host"`
	IP    string                `json:"ip"`
	Ports map[string]portResult `json:"ports"`
}

func parsePorts(s string) ([]int, error) {
	var out []int
	seen := map[int]bool{}
	for _, part := range strings.Split(s, ",") {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}
		if strings.Contains(part, "-") {
			b := strings.SplitN(part, "-", 2)
			a, err1 := strconv.Atoi(strings.TrimSpace(b[0]))
			z, err2 := strconv.Atoi(strings.TrimSpace(b[1]))
			if err1 != nil || err2 != nil || a < 1 || z > 65535 || a > z {
				return nil, fmt.Errorf("rango no válido: %s", part)
			}
			if z-a > 2048 {
				return nil, fmt.Errorf("rango muy grande (máx 2048 puertos)")
			}
			for p := a; p <= z; p++ {
				if !seen[p] {
					seen[p] = true
					out = append(out, p)
				}
			}
		} else {
			p, err := strconv.Atoi(part)
			if err != nil || p < 1 || p > 65535 {
				return nil, fmt.Errorf("puerto no válido: %s", part)
			}
			if !seen[p] {
				seen[p] = true
				out = append(out, p)
			}
		}
		if len(out) > 2048 {
			return nil, fmt.Errorf("demasiados puertos en total (máx 2048 puertos por escaneo)")
		}
	}
	sort.Ints(out)
	return out, nil
}

func grabBanner(conn net.Conn, port int, timeout time.Duration) string {
	conn.SetDeadline(time.Now().Add(timeout))
	if port == 80 || port == 8080 || port == 8000 {
		conn.Write([]byte("HEAD / HTTP/1.0\r\nHost: x\r\n\r\n"))
	}
	if port == 443 {
		return "443/tcp: TLS (banner cifrado)"
	}
	buf := make([]byte, 512)
	n, err := conn.Read(buf)
	if err != nil || n == 0 {
		return "abierto (sin banner)"
	}
	line := strings.SplitN(string(bytes.TrimSpace(buf[:n])), "\n", 2)[0]
	line = strings.Map(func(r rune) rune {
		if r < 32 || r == 127 {
			return -1
		}
		return r
	}, line)
	if len(line) > 200 {
		line = line[:200]
	}
	if line == "" {
		return "abierto (banner vacío)"
	}
	return line
}

func cmdScan(args []string) {
	fs := flag.NewFlagSet("scan", flag.ExitOnError)
	host := fs.String("host", "", "host o IP")
	ports := fs.String("ports", "22,80,443", "puertos: 22,80 o 1-1024")
	timeoutMs := fs.Int("timeout", 1000, "timeout ms por puerto")
	workers := fs.Int("workers", 100, "conexiones simultáneas")
	fs.Parse(args)

	if *host == "" || *ports == "" {
		fmt.Fprintln(os.Stderr, "scan requiere --host y --ports")
		os.Exit(2)
	}
	plist, err := parsePorts(*ports)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	timeout := time.Duration(*timeoutMs) * time.Millisecond

	ip := *host
	if net.ParseIP(ip) == nil {
		addrs, err := net.ResolveIPAddr("ip", *host)
		if err != nil {
			emitJSON(scanOut{Host: *host, IP: "", Ports: map[string]portResult{}})
			fmt.Fprintln(os.Stderr, "no se pudo resolver:", err)
			os.Exit(1)
		}
		ip = addrs.String()
	}

	type job struct{ port int }
	jobs := make(chan job)
	var mu sync.Mutex
	results := map[string]portResult{}
	var wg sync.WaitGroup
	for i := 0; i < *workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := range jobs {
				addr := net.JoinHostPort(ip, strconv.Itoa(j.port))
				conn, err := net.DialTimeout("tcp", addr, timeout)
				key := strconv.Itoa(j.port)
				if err != nil {
					mu.Lock()
					results[key] = portResult{Open: false}
					mu.Unlock()
					continue
				}
				banner := grabBanner(conn, j.port, timeout)
				conn.Close()
				mu.Lock()
				results[key] = portResult{Open: true, Banner: banner}
				mu.Unlock()
			}
		}()
	}
	go func() {
		for _, p := range plist {
			jobs <- job{port: p}
		}
		close(jobs)
	}()
	wg.Wait()
	emitJSON(scanOut{Host: *host, IP: ip, Ports: results})
}

// ---------- DNS ----------

type dnsOut struct {
	Host   string   `json:"host"`
	IP     string   `json:"ip,omitempty"`
	IPs    []string `json:"ips,omitempty"`
	Fuente string   `json:"fuente"`
	Error  string   `json:"error,omitempty"`
}

type dohResp struct {
	Answer []struct {
		Type int    `json:"type"`
		Data string `json:"data"`
	} `json:"Answer"`
}

func cmdDNS(args []string) {
	fs := flag.NewFlagSet("dns", flag.ExitOnError)
	host := fs.String("host", "", "host a resolver")
	fs.Parse(args)
	if *host == "" {
		fmt.Fprintln(os.Stderr, "dns requiere --host")
		os.Exit(2)
	}
	// 1) Sistema
	if addrs, err := net.LookupHost(*host); err == nil && len(addrs) > 0 {
		emitJSON(dnsOut{Host: *host, IP: addrs[0], IPs: addrs, Fuente: "sistema"})
		return
	}
	// 2) Respaldo DoH (one.one.one.one primero: otros endpoints suelen ser interceptados)
	client := &http.Client{Timeout: 8 * time.Second}
	req, _ := http.NewRequest("GET",
		"https://one.one.one.one/dns-query?name="+*host+"&type=A", nil)
	req.Header.Set("Accept", "application/dns-json")
	resp, err := client.Do(req)
	if err != nil {
		emitJSON(dnsOut{Host: *host, Fuente: "fallo", Error: err.Error()})
		os.Exit(1)
	}
	defer resp.Body.Close()
	var d dohResp
	if err := json.NewDecoder(resp.Body).Decode(&d); err != nil || len(d.Answer) == 0 {
		emitJSON(dnsOut{Host: *host, Fuente: "fallo", Error: "sin respuesta DoH"})
		os.Exit(1)
	}
	var ips []string
	for _, a := range d.Answer {
		if a.Type == 1 || a.Type == 28 {
			ips = append(ips, a.Data)
		}
	}
	if len(ips) == 0 {
		emitJSON(dnsOut{Host: *host, Fuente: "fallo", Error: "sin registros A/AAAA"})
		os.Exit(1)
	}
	emitJSON(dnsOut{Host: *host, IP: ips[0], IPs: ips, Fuente: "DoH-cloudflare"})
}

func emitJSON(v any) {
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	enc.Encode(v)
}
