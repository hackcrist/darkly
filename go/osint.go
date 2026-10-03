// osint.go: geoIP multi-fuente, PTR preciso, RDAP, WHOIS, búsqueda de usuarios.
package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"
)

var browserUA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

func getJSON(urlStr string, timeout time.Duration) (map[string]any, error) {
	client := &http.Client{Timeout: timeout}
	req, _ := http.NewRequest("GET", urlStr, nil)
	req.Header.Set("User-Agent", "darkly-go/2.1 (educativo)")
	req.Header.Set("Accept", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var out map[string]any
	if err := json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&out); err != nil {
		return nil, err
	}
	return out, nil
}

// ---------- geo ----------

func normGeo(data map[string]any) map[string]any {
	if _, ok := data["latitude"]; ok {
		if _, has := data["lat"]; !has {
			data["lat"] = data["latitude"]
			data["lon"] = data["longitude"]
			data["query"] = data["ip"]
			if conn, ok := data["connection"].(map[string]any); ok {
				data["org"] = firstStr(conn["org"], conn["isp"])
				data["isp"] = firstStr(conn["isp"])
			}
		}
	}
	return data
}

func geoCore(ip string) map[string]any {
	ip = strings.TrimSpace(ip)
	if net.ParseIP(ip) == nil {
		return map[string]any{"error": fmt.Sprintf("'%s' no es una IP válida (ej. 8.8.8.8)", ip)}
	}
	fuentes := []string{
		"http://ip-api.com/json/" + url.PathEscape(ip) + "?fields=status,message,country,regionName,city,lat,lon,org,isp,query",
		"https://ipapi.co/" + url.PathEscape(ip) + "/json/",
		"https://ipwho.is/" + url.PathEscape(ip),
	}
	var ultimo string
	for _, u := range fuentes {
		if data, err := getJSON(u, 10*time.Second); err == nil {
			data = normGeo(data)
			data["fuente"] = u
			return data
		} else {
			ultimo = u + ": " + err.Error()
		}
	}
	return map[string]any{"error": "Todas las fuentes fallaron. " + ultimo}
}

func cmdIPInfo(args []string) {
	fs := flag.NewFlagSet("ipinfo", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go ipinfo <ip>  |  darkly-go ipinfo --mia")
		os.Exit(2)
	}
	if fs.Arg(0) == "--mia" || fs.Arg(0) == "mia" {
		for _, u := range []string{
			"http://ip-api.com/json/?fields=status,message,country,regionName,city,query,org,isp",
			"https://ipapi.co/json/",
			"https://ipwho.is/json/",
		} {
			if data, err := getJSON(u, 10*time.Second); err == nil {
				data = normGeo(data)
				data["fuente"] = u
				emitJSON(data)
				return
			}
		}
		emitJSON(map[string]string{"error": "Todas las fuentes fallaron. Revisa tu internet/DNS."})
		return
	}
	emitJSON(geoCore(fs.Arg(0)))
}

// ---------- PTR ----------

func ptrCore(ip string) string {
	ip = strings.Trim(strings.TrimSpace(ip), "[]")
	addr := net.ParseIP(ip)
	if addr == nil {
		return fmt.Sprintf("[!] '%s' no es una IP válida (ej. 8.8.8.8)", ip)
	}
	if addr.IsLoopback() {
		return "localhost (loopback, sin PTR público)"
	}
	if addr.IsPrivate() {
		return "IP privada RFC1918 (sin PTR público; solo tu router la conoce)"
	}
	if addr.IsMulticast() || addr.IsLinkLocalUnicast() || addr.IsUnspecified() {
		return "IP reservada/especial (sin PTR público esperado)"
	}
	if names, err := net.LookupAddr(ip); err == nil && len(names) > 0 {
		return strings.TrimSuffix(names[0], ".") + " (fuente: sistema)"
	} else {
		ultimo := err.Error()
		// Respaldo DoH
		var rev string
		if addr.To4() != nil {
			parts := strings.Split(ip, ".")
			for i, j := 0, len(parts)-1; i < j; i, j = i+1, j-1 {
				parts[i], parts[j] = parts[j], parts[i]
			}
			rev = strings.Join(parts, ".") + ".in-addr.arpa"
		} else {
			b := addr.To16()
			var nib []string
			for i := len(b) - 1; i >= 0; i-- {
				nib = append(nib, fmt.Sprintf("%x", b[i]&0xf), fmt.Sprintf("%x", b[i]>>4))
			}
			rev = strings.Join(nib, ".") + ".ip6.arpa"
		}
		client := &http.Client{Timeout: 8 * time.Second}
		for _, base := range []string{"https://one.one.one.one/dns-query?name=", "https://cloudflare-dns.com/dns-query?name=", "https://dns.google/resolve?name="} {
			req, _ := http.NewRequest("GET", base+rev+"&type=PTR", nil)
			req.Header.Set("Accept", "application/dns-json")
			resp, err := client.Do(req)
			if err != nil {
				continue
			}
			var d dohResp2
			if err := json.NewDecoder(io.LimitReader(resp.Body, 65536)).Decode(&d); err != nil {
				resp.Body.Close()
				continue
			}
			resp.Body.Close()
			for _, a := range d.Answer {
				if strings.TrimSuffix(a.Data, ".") != "" {
					return strings.TrimSuffix(a.Data, ".") + " (fuente: DoH)"
				}
			}
		}
		return fmt.Sprintf("[!] Sin registro PTR para %s (el dueño no creó reverso). Detalle: %s", ip, ultimo)
	}
}

func cmdPTR(args []string) {
	fs := flag.NewFlagSet("ptr", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go ptr <ip>")
		os.Exit(2)
	}
	emitJSON(map[string]string{"ip": fs.Arg(0), "ptr": ptrCore(fs.Arg(0))})
}

// ---------- RDAP ----------

func rdapCore(q string) map[string]any {
	q = strings.ToLower(strings.Trim(strings.TrimSpace(q), "."))
	if q == "" {
		return map[string]any{"error": "Consulta vacía"}
	}
	if strings.Contains(q, "://") {
		parts := strings.SplitN(q, "://", 2)
		q = parts[1]
	}
	q = strings.Split(q, "/")[0]
	q = strings.Split(q, ":")[0]

	var urls []string
	if net.ParseIP(q) != nil {
		urls = []string{
			"https://rdap.org/ip/" + url.PathEscape(q),
			"https://rdap.db.ripe.net/ip/" + url.PathEscape(q),
			"https://rdap.arin.net/registry/ip/" + url.PathEscape(q),
		}
	} else if strings.Contains(q, ".") {
		urls = []string{"https://rdap.org/domain/" + url.PathEscape(q)}
		if strings.HasSuffix(q, ".com") || strings.HasSuffix(q, ".net") {
			urls = append(urls, "https://rdap.verisign.com/com/v1/domain/"+url.PathEscape(q))
		}
	} else {
		return map[string]any{"error": "Dame un dominio (ej. google.com) o IP (ej. 8.8.8.8)"}
	}

	var lastErr error
	for _, u := range urls {
		data, err := getJSON(u, 12*time.Second)
		if err == nil {
			out := map[string]any{"fuente": u, "nombre": firstStr(data["name"], data["ldhName"], data["handle"]), "estado": data["status"]}
			if ents, ok := data["entities"].([]any); ok {
				out["registros"] = len(ents)
			}
			if evs, ok := data["events"].([]any); ok {
				for _, e := range evs {
					if m, ok := e.(map[string]any); ok {
						if m["eventAction"] == "registration" || m["eventAction"] == "expiration" || m["eventAction"] == "last changed" {
							out[m["eventAction"].(string)] = m["eventDate"]
						}
					}
				}
			}
			return out
		}
		lastErr = err
	}
	return map[string]any{"error": "RDAP falló: " + lastErr.Error()}
}

func firstStr(v ...any) any {
	for _, x := range v {
		if s, ok := x.(string); ok && s != "" {
			return s
		}
	}
	return nil
}

func cmdRDAP(args []string) {
	fs := flag.NewFlagSet("rdap", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go rdap <dominio|ip>")
		os.Exit(2)
	}
	emitJSON(rdapCore(fs.Arg(0)))
}

// ---------- WHOIS ----------

func whoisAsk(server, q string, timeout time.Duration) (string, error) {
	conn, err := net.DialTimeout("tcp", server+":43", timeout)
	if err != nil {
		return "", err
	}
	defer conn.Close()
	conn.SetDeadline(time.Now().Add(timeout))
	fmt.Fprintf(conn, "%s\r\n", q)
	var sb strings.Builder
	br := bufio.NewReader(conn)
	for sb.Len() < 16384 {
		chunk := make([]byte, 4096)
		n, err := br.Read(chunk)
		if n > 0 {
			sb.Write(chunk[:n])
		}
		if err != nil {
			break
		}
	}
	return sb.String(), nil
}

func cmdWhois(args []string) {
	fs := flag.NewFlagSet("whois", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go whois <dominio|ip>")
		os.Exit(2)
	}
	q := strings.ToLower(strings.TrimSpace(fs.Arg(0)))
	if ok, _ := regexp.MatchString(`^[a-z0-9.\-:]+$`, q); !ok || q == "" {
		fmt.Fprintln(os.Stderr, "Caracteres no válidos en dominio/IP")
		os.Exit(2)
	}
	resp, err := whoisAsk("whois.iana.org", q, 10*time.Second)
	if err != nil {
		emitJSON(map[string]string{"error": "WHOIS falló (el puerto 43 puede estar bloqueado): " + err.Error()})
		os.Exit(1)
	}
	var refer string
	for _, line := range strings.Split(resp, "\n") {
		low := strings.ToLower(line)
		if strings.HasPrefix(low, "refer:") || strings.HasPrefix(low, "whois:") {
			refer = strings.TrimSpace(line[strings.Index(line, ":")+1:])
			break
		}
	}
	if refer != "" {
		if r2, err := whoisAsk(refer, q, 10*time.Second); err == nil {
			resp += "\n\n--- referencia: " + refer + " ---\n" + r2
		} else {
			resp += fmt.Sprintf("\n[!] referencia %s falló: %v", refer, err)
		}
	}
	if len(resp) > 8000 {
		resp = resp[:8000]
	}
	emitJSON(map[string]string{"query": q, "whois": resp})
}

// ---------- búsqueda de usuarios ----------

type userSite struct {
	name, tpl, level string
}

var userSites = []userSite{
	{"GitHub", "https://github.com/{u}", "firme"},
	{"GitLab", "https://gitlab.com/{u}", "firme"},
	{"PyPI", "https://pypi.org/user/{u}/", "firme"},
	{"DockerHub", "https://hub.docker.com/u/{u}", "firme"},
	{"Reddit", "https://www.reddit.com/user/{u}/", "firme"},
	{"Twitch", "https://www.twitch.tv/{u}", "firme"},
	{"Pinterest", "https://www.pinterest.com/{u}/", "firme"},
	{"Vimeo", "https://vimeo.com/{u}", "firme"},
	{"SoundCloud", "https://soundcloud.com/{u}", "indicio"},
	{"Chess.com", "https://www.chess.com/member/{u}", "firme"},
	{"Telegram", "https://t.me/{u}", "indicio"},
	{"Medium", "https://medium.com/@{u}", "indicio"},
	{"TikTok", "https://www.tiktok.com/@{u}", "indicio"},
	{"Instagram", "https://www.instagram.com/{u}/", "indicio"},
	{"X", "https://x.com/{u}", "indicio"},
	{"YouTube", "https://www.youtube.com/@{u}", "indicio"},
}

var notFoundMarks = []string{
	"not found", "page not found", "nobody on reddit",
	"doesn't exist", "couldn't find", "no hemos encontrado",
	"usuario no encontrado", "this account doesn't exist",
	"sorry, this page isn't available",
}

func checkUserSite(name, rawurl string) (estado, final string) {
	client := &http.Client{Timeout: 10 * time.Second, CheckRedirect: func(req *http.Request, via []*http.Request) error {
		if len(via) >= 5 {
			return http.ErrUseLastResponse
		}
		return nil
	}}
	req, _ := http.NewRequest("GET", rawurl, nil)
	req.Header.Set("User-Agent", browserUA)
	req.Header.Set("Accept", "text/html,application/xhtml+xml,*/*")
	resp, err := client.Do(req)
	if err != nil {
		msg := err.Error()
		switch {
		case strings.Contains(msg, "404") || strings.Contains(msg, "Not Found"):
			return "no existe", rawurl
		case strings.Contains(msg, "429") || strings.Contains(msg, "Too Many"):
			return "limitado (429)", rawurl
		case strings.Contains(msg, "403") || strings.Contains(msg, "Forbidden"):
			return "bloqueado (403)", rawurl
		default:
			if len(msg) > 80 {
				msg = msg[:80]
			}
			return "error: " + msg, rawurl
		}
	}
	defer resp.Body.Close()
	finalURL := resp.Request.URL.String()
	if resp.StatusCode == 404 {
		return "no existe", rawurl
	}
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 6000))
	low := strings.ToLower(string(body))
	for _, m := range notFoundMarks {
		if strings.Contains(low, m) {
			return "no existe", rawurl
		}
	}
	if finalURL != rawurl && (strings.Contains(strings.ToLower(finalURL), "login") || strings.Contains(strings.ToLower(finalURL), "signin")) {
		return "bloqueado-login", rawurl
	}
	return "posible perfil", finalURL
}

func checkNPM(u string) (string, string) {
	data, err := getJSON("https://registry.npmjs.org/-/v1/search?text=maintainer:"+url.QueryEscape(u)+"&size=1", 10*time.Second)
	if err != nil {
		msg := err.Error()
		if len(msg) > 80 {
			msg = msg[:80]
		}
		return "error: " + msg, "https://www.npmjs.com/~" + u
	}
	if total, _ := data["total"].(float64); total > 0 {
		return fmt.Sprintf("posible perfil (%d paquetes)", int(total)), "https://www.npmjs.com/~" + u
	}
	return "sin paquetes (puede existir sin publicar)", "https://www.npmjs.com/~" + u
}

type userResult struct {
	Sitio  string `json:"sitio"`
	Estado string `json:"estado"`
	URL    string `json:"url"`
}

func userSearch(u string) []userResult {
	var mu sync.Mutex
	var out []userResult
	var wg sync.WaitGroup
	sem := make(chan struct{}, 6)
	run := func(name, rawurl, level string) {
		defer wg.Done()
		sem <- struct{}{}
		defer func() { <-sem }()
		estado, final := checkUserSite(name, rawurl)
		if estado == "posible perfil" && level == "indicio" {
			estado = "posible perfil (indicio, verificar a mano)"
		}
		mu.Lock()
		out = append(out, userResult{name, estado, final})
		mu.Unlock()
	}
	for _, s := range userSites {
		wg.Add(1)
		go run(s.name, strings.ReplaceAll(s.tpl, "{u}", u), s.level)
	}
	wg.Add(1)
	go func() {
		defer wg.Done()
		sem <- struct{}{}
		defer func() { <-sem }()
		estado, final := checkNPM(u)
		mu.Lock()
		out = append(out, userResult{"npm", estado, final})
		mu.Unlock()
	}()
	wg.Wait()
	rank := func(e string) int {
		if e == "posible perfil" {
			return 0
		}
		if strings.HasPrefix(e, "posible perfil") {
			return 1
		}
		return 2
	}
	sort.Slice(out, func(i, j int) bool {
		if rank(out[i].Estado) != rank(out[j].Estado) {
			return rank(out[i].Estado) < rank(out[j].Estado)
		}
		return out[i].Sitio < out[j].Sitio
	})
	return out
}

func cmdUser(args []string) {
	fs := flag.NewFlagSet("user", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go user <nombre>")
		os.Exit(2)
	}
	u := strings.TrimPrefix(strings.TrimSpace(fs.Arg(0)), "@")
	if ok, _ := regexp.MatchString(`^[A-Za-z0-9._-]{2,30}$`, u); !ok {
		fmt.Fprintln(os.Stderr, "Usuario no válido: usa 2-30 caracteres (letras, números, . _ -)")
		os.Exit(2)
	}
	emitJSON(map[string]any{"usuario": u, "resultados": userSearch(u)})
}

// ---------- registros DNS ----------

var domainRe = regexp.MustCompile(`^[a-z0-9.-]+\.[a-z]{2,}$`)

func cleanDomain(d string) (string, error) {
	d = strings.ToLower(strings.TrimSpace(d))
	d = strings.TrimPrefix(d, "http://")
	d = strings.TrimPrefix(d, "https://")
	if i := strings.Index(d, "/"); i >= 0 {
		d = d[:i]
	}
	if i := strings.Index(d, ":"); i >= 0 {
		d = d[:i]
	}
	d = strings.TrimPrefix(d, "www.")
	if strings.HasPrefix(d, "-") || !domainRe.MatchString(d) {
		return "", fmt.Errorf("'%s' no parece un dominio válido (ej. google.com)", d)
	}
	return d, nil
}

func dohType(domain, rtype string) []string {
	for _, base := range []string{"https://one.one.one.one/dns-query?name=", "https://cloudflare-dns.com/dns-query?name="} {
		client := &http.Client{Timeout: 8 * time.Second}
		req, _ := http.NewRequest("GET", base+url.QueryEscape(domain)+"&type="+rtype, nil)
		req.Header.Set("Accept", "application/dns-json")
		resp, err := client.Do(req)
		if err != nil {
			continue
		}
		var d dohResp2
		if err := json.NewDecoder(io.LimitReader(resp.Body, 65536)).Decode(&d); err != nil {
			resp.Body.Close()
			continue
		}
		resp.Body.Close()
		var out []string
		for _, a := range d.Answer {
			if a.Data != "" {
				out = append(out, a.Data)
			}
		}
		if len(out) > 0 {
			return out
		}
	}
	return nil
}

func cmdDNSRecords(args []string) {
	fs := flag.NewFlagSet("dnsrecords", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go dnsrecords <dominio>")
		os.Exit(2)
	}
	d, err := cleanDomain(fs.Arg(0))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	out := map[string]any{"dominio": d}
	for _, rt := range []string{"A", "MX", "TXT", "NS"} {
		if ans := dohType(d, rt); len(ans) > 0 {
			out[rt] = ans
		} else {
			out[rt] = []string{"(sin registros)"}
		}
	}
	emitJSON(out)
}

// ---------- subdominios crt.sh ----------

func cmdSubdomains(args []string) {
	fs := flag.NewFlagSet("subdomains", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go subdomains <dominio>")
		os.Exit(2)
	}
	d, err := cleanDomain(fs.Arg(0))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	subs, cerr := crtList(d)
	if cerr != nil {
		emitJSON(map[string]any{"dominio": d, "error": "crt.sh falló: " + cerr.Error()})
		os.Exit(1)
	}
	emitJSON(map[string]any{"dominio": d, "total": len(subs), "subdominios": subs})
}

func crtList(d string) ([]string, error) {
	client := &http.Client{Timeout: 20 * time.Second}
	var lastErr error
	var list []map[string]any
	for intento := 0; intento < 3; intento++ {
		if intento > 0 {
			time.Sleep(3 * time.Second)
		}
		req, _ := http.NewRequest("GET", "https://crt.sh/?q=%25."+url.PathEscape(d)+"&output=json", nil)
		req.Header.Set("Accept", "application/json")
		req.Header.Set("User-Agent", "darkly-go/2.1 (educativo)")
		resp, err := client.Do(req)
		if err != nil {
			lastErr = err
			continue
		}
		list = nil
		err = json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&list)
		resp.Body.Close()
		if err != nil {
			lastErr = err
			continue
		}
		lastErr = nil
		break
	}
	if lastErr != nil {
		// Respaldo gratis: HackerTarget hostsearch
		if fb := hackertargetSubs(d); len(fb) > 0 {
			if len(fb) > 50 {
				fb = fb[:50]
			}
			return fb, nil
		}
		return nil, lastErr
	}
	set := map[string]bool{}
	for _, e := range list {
		for _, line := range strings.Split(fmt.Sprintf("%v", e["name_value"]), "\n") {
			s := strings.ToLower(strings.TrimSpace(strings.TrimLeft(line, "*.")))
			if s != "" && (s == d || strings.HasSuffix(s, "."+d)) {
				set[s] = true
			}
		}
	}
	var subs []string
	for s := range set {
		subs = append(subs, s)
	}
	sort.Strings(subs)
	if len(subs) > 50 {
		subs = subs[:50]
	}
	return subs, nil
}

func hackertargetSubs(d string) []string {
	client := &http.Client{Timeout: 10 * time.Second}
	req, _ := http.NewRequest("GET", "https://api.hackertarget.com/hostsearch/?q="+url.QueryEscape(d), nil)
	req.Header.Set("User-Agent", "darkly-go/2.1 (educativo)")
	resp, err := client.Do(req)
	if err != nil {
		return nil
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 1 << 20))
	set := map[string]bool{}
	for _, line := range strings.Split(string(body), "\n") {
		h := strings.ToLower(strings.TrimSpace(strings.TrimLeft(strings.SplitN(line, ",", 2)[0], "*.")))
		if h != "" && (h == d || strings.HasSuffix(h, "."+d)) {
			set[h] = true
		}
	}
	var subs []string
	for s := range set {
		subs = append(subs, s)
	}
	sort.Strings(subs)
	return subs
}

// ---------- perfil GitHub ----------
func cmdGHUser(args []string) {
	fs := flag.NewFlagSet("ghuser", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go ghuser <usuario>")
		os.Exit(2)
	}
	u := strings.TrimPrefix(strings.TrimSpace(fs.Arg(0)), "@")
	if ok, _ := regexp.MatchString(`^[A-Za-z0-9-]{1,39}$`, u); !ok {
		fmt.Fprintln(os.Stderr, "Usuario GitHub no válido")
		os.Exit(2)
	}
	data, err := getJSON("https://api.github.com/users/"+url.PathEscape(u), 10*time.Second)
	if err != nil {
		emitJSON(map[string]string{"error": "GitHub API falló: " + err.Error()})
		os.Exit(1)
	}
	if data["message"] == "Not Found" {
		emitJSON(map[string]string{"usuario": u, "error": "No existe ese usuario en GitHub"})
		os.Exit(1)
	}
	out := map[string]any{}
	for _, k := range []string{"login", "name", "company", "blog", "location", "email", "bio", "public_repos", "followers", "following", "created_at", "html_url"} {
		if v, ok := data[k]; ok {
			out[k] = v
		} else {
			out[k] = "-"
		}
	}
	emitJSON(out)
}
