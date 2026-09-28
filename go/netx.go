// netx.go: ping, subredes, traceroute + núcleos reutilizables (dns, ping, scan).
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/exec"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode/utf8"

	"golang.org/x/text/encoding/charmap"
	"golang.org/x/text/transform"
)

// ---------- ping ----------

func pingCore(host string) string {
	host = strings.TrimSpace(host)
	if host == "" {
		return "[!] Host vacío"
	}
	if ok, _ := regexp.MatchString(`^[A-Za-z0-9.\-:]+$`, host); !ok {
		return "[!] Host no válido (solo letras, números, puntos, guiones)"
	}
	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		cmd = exec.Command("ping", "-n", "2", "-w", "2000", host)
	} else {
		cmd = exec.Command("ping", "-c", "2", "-W", "2", host)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	cmd = exec.CommandContext(ctx, cmd.Args[0], cmd.Args[1:]...)
	out, err := cmd.CombinedOutput()
	if err != nil && len(out) == 0 {
		return fmt.Sprintf("[!] falló el ping: %v", err)
	}
	return decodeConsole(out)
}

func cmdPing(args []string) {
	fs := flag.NewFlagSet("ping", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go ping <host>")
		os.Exit(2)
	}
	emitJSON(map[string]string{"host": fs.Arg(0), "salida": pingCore(fs.Arg(0))})
}

// ---------- subnet ----------

func subnetCore(cidr string) (map[string]any, error) {
	cidr = strings.TrimSpace(cidr)
	ip, ipnet, err := net.ParseCIDR(cidr)
	if err != nil {
		return nil, fmt.Errorf("CIDR no válido '%s': %v", cidr, err)
	}
	ones, bits := ipnet.Mask.Size()
	total := uint64(1) << uint(bits-ones)
	maskStr := net.IP(ipnet.Mask).String()
	ver := "IPv4"
	if ip.To4() == nil {
		ver = "IPv6"
	}
	out := map[string]any{
		"network":          ipnet.IP.String(),
		"netmask":          maskStr,
		"prefix":           ones,
		"total_addresses":  total,
		"version":          ver,
	}
	if ver == "IPv4" {
		base := ipToUint32(ipnet.IP.To4())
		m := ipToUint32(net.IP(ipnet.Mask).To4())
		bc := net.IPv4(byte(base>>24), byte(base>>16), byte(base>>8), byte(base))
		_ = bc
		bcast := base | ^m
		out["broadcast"] = uint32ToIP(bcast).String()
		var usable uint64
		if total >= 2 {
			usable = total - 2
		}
		out["usable_hosts"] = usable
		if usable > 0 {
			out["first_host"] = uint32ToIP(base + 1).String()
			out["last_host"] = uint32ToIP(bcast - 1).String()
		} else {
			out["first_host"] = "n/a"
			out["last_host"] = "n/a"
		}
	} else {
		out["broadcast"] = "n/a (IPv6)"
		out["usable_hosts"] = total
		out["first_host"] = ipnet.IP.String()
		out["last_host"] = "n/a (IPv6)"
	}
	return out, nil
}

func ipToUint32(ip net.IP) uint32 {
	b := ip.To4()
	return uint32(b[0])<<24 | uint32(b[1])<<16 | uint32(b[2])<<8 | uint32(b[3])
}

func uint32ToIP(n uint32) net.IP {
	return net.IPv4(byte(n>>24), byte(n>>16), byte(n>>8), byte(n))
}

func cmdSubnet(args []string) {
	fs := flag.NewFlagSet("subnet", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go subnet 192.168.1.0/24")
		os.Exit(2)
	}
	out, err := subnetCore(fs.Arg(0))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	emitJSON(out)
}

// ---------- traceroute ----------

func cmdTraceroute(args []string) {
	fs := flag.NewFlagSet("traceroute", flag.ExitOnError)
	hops := fs.Int("hops", 20, "saltos máximos")
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go traceroute <host>")
		os.Exit(2)
	}
	host := strings.TrimSpace(fs.Arg(0))
	if ok, _ := regexp.MatchString(`^[A-Za-z0-9.\-:]+$`, host); !ok {
		emitJSON(map[string]string{"host": host, "salida": "[!] Host no válido"})
		return
	}
	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		cmd = exec.Command("tracert", "-d", "-h", strconv.Itoa(*hops), "-w", "2000", host)
	} else {
		bin, err := exec.LookPath("traceroute")
		if err != nil {
			emitJSON(map[string]string{"host": host, "salida": "[!] 'traceroute' no encontrado. Instálalo: sudo apt install traceroute"})
			return
		}
		cmd = exec.Command(bin, "-n", "-m", strconv.Itoa(*hops), "-w", "2", host)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()
	cmd = exec.CommandContext(ctx, cmd.Args[0], cmd.Args[1:]...)
	out, err := cmd.CombinedOutput()
	if err != nil && len(out) == 0 {
		emitJSON(map[string]string{"host": host, "salida": fmt.Sprintf("[!] falló traceroute: %v", err)})
		return
	}
	emitJSON(map[string]string{"host": host, "salida": decodeConsole(out)})
}

// ---------- decodificación consola Windows (OEM -> UTF-8) ----------

func oemCodePage() string {
	// ping/tracert escriben en codepage OEM aunque la salida vaya por pipe.
	out, err := exec.Command("cmd", "/c", "chcp").Output()
	if err != nil {
		return "850"
	}
	// "Página de códigos activa: 850." -> toma el último grupo de dígitos.
	all, cur := "", ""
	for _, c := range string(out) {
		if c >= '0' && c <= '9' {
			cur += string(c)
		} else {
			if cur != "" {
				all = cur
			}
			cur = ""
		}
	}
	if cur != "" {
		all = cur
	}
	if all == "" {
		return "850"
	}
	return all
}

func decodeConsole(b []byte) string {
	if utf8.Valid(b) {
		return string(b)
	}
	var dec *charmap.Charmap
	switch oemCodePage() {
	case "437":
		dec = charmap.CodePage437
	case "866":
		dec = charmap.CodePage866
	case "1252":
		dec = charmap.Windows1252
	default:
		dec = charmap.CodePage850
	}
	out, _, err := transform.Bytes(dec.NewDecoder(), b)
	if err != nil {
		return string(b)
	}
	return string(out)
}

// ---------- núcleos para reportes ----------

type dohResp2 struct {
	Answer []struct {
		Type int    `json:"type"`
		Data string `json:"data"`
	} `json:"Answer"`
}

func dnsCore(host string) map[string]any {
	host = strings.TrimSpace(host)
	out := map[string]any{"host": host}
	if addrs, err := net.LookupHost(host); err == nil && len(addrs) > 0 {
		out["ip"] = addrs[0]
		out["todas_ips"] = addrs
		out["fuente"] = "sistema"
		return out
	}
	client := &http.Client{Timeout: 8 * time.Second}
	req, _ := http.NewRequest("GET", "https://one.one.one.one/dns-query?name="+host+"&type=A", nil)
	req.Header.Set("Accept", "application/dns-json")
	resp, err := client.Do(req)
	if err != nil {
		out["error"] = "DNS falló (sistema + DoH): " + err.Error()
		return out
	}
	defer resp.Body.Close()
	var d dohResp2
	if err := json.NewDecoder(resp.Body).Decode(&d); err != nil || len(d.Answer) == 0 {
		out["error"] = "Sin respuesta DNS ni por DoH"
		return out
	}
	var ips []string
	for _, a := range d.Answer {
		if a.Type == 1 || a.Type == 28 {
			ips = append(ips, a.Data)
		}
	}
	if len(ips) == 0 {
		out["error"] = "Sin registros A/AAAA"
		return out
	}
	out["ip"] = ips[0]
	out["todas_ips"] = ips
	out["fuente"] = "DoH-cloudflare"
	return out
}

func scanCore(host string, plist []int, timeoutMs, workers int) (string, map[string]map[string]any) {
	timeout := time.Duration(timeoutMs) * time.Millisecond
	ip := host
	if net.ParseIP(ip) == nil {
		if a, err := net.ResolveIPAddr("ip", host); err == nil {
			ip = a.String()
		} else {
			return "", map[string]map[string]any{"error": {"mensaje": "no se pudo resolver: " + err.Error()}}
		}
	}
	jobs := make(chan int)
	var mu sync.Mutex
	res := map[string]map[string]any{}
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for p := range jobs {
				conn, err := net.DialTimeout("tcp", net.JoinHostPort(ip, strconv.Itoa(p)), timeout)
				key := strconv.Itoa(p)
				if err != nil {
					mu.Lock()
					res[key] = map[string]any{"open": false}
					mu.Unlock()
					continue
				}
				b := grabBanner(conn, p, timeout)
				conn.Close()
				mu.Lock()
				res[key] = map[string]any{"open": true, "banner": b}
				mu.Unlock()
			}
		}()
	}
	go func() {
		for _, p := range plist {
			jobs <- p
		}
		close(jobs)
	}()
	wg.Wait()
	return ip, res
}
