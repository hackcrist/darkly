// sec.go: hash, identificación, contraseñas, cabeceras, URL, filtraciones.
package main

import (
	"crypto/md5"
	"crypto/rand"
	"crypto/sha1"
	"crypto/sha256"
	"crypto/sha512"
	"encoding/hex"
	"flag"
	"fmt"
	"hash"
	"math/big"
	"net"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"strings"
	"sync"
)

// ---------- hash ----------

func cmdHash(args []string) {
	fs := flag.NewFlagSet("hash", flag.ExitOnError)
	algo := fs.String("algo", "sha256", "md5|sha1|sha256|sha512")
	fs.Parse(args)
	text := strings.Join(fs.Args(), " ")
	if text == "" {
		fmt.Fprintln(os.Stderr, "uso: darkly-go hash --algo sha256 <texto>")
		os.Exit(2)
	}
	var h hash.Hash
	switch strings.ToLower(strings.ReplaceAll(*algo, "-", "")) {
	case "md5":
		h = md5.New()
	case "sha1":
		h = sha1.New()
	case "sha256":
		h = sha256.New()
	case "sha512":
		h = sha512.New()
	default:
		fmt.Fprintln(os.Stderr, "Algoritmo no soportado. Usa md5, sha1, sha256, sha512")
		os.Exit(2)
	}
	h.Write([]byte(text))
	emitJSON(map[string]string{"algo": *algo, "hex": hex.EncodeToString(h.Sum(nil))})
}

// ---------- hashid ----------

var hashPatterns = []struct{ name, pat string }{
	{"MD5 (32 hex)", "^[a-fA-F0-9]{32}$"},
	{"SHA-1 (40 hex)", "^[a-fA-F0-9]{40}$"},
	{"SHA-256 (64 hex)", "^[a-fA-F0-9]{64}$"},
	{"SHA-512 (128 hex)", "^[a-fA-F0-9]{128}$"},
}

func cmdHashID(args []string) {
	fs := flag.NewFlagSet("hashid", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go hashid <hash>")
		os.Exit(2)
	}
	h := strings.TrimSpace(fs.Arg(0))
	var out []string
	for _, r := range hashPatterns {
		if ok, _ := regexp.MatchString(r.pat, h); ok {
			out = append(out, r.name)
		}
	}
	if out == nil {
		out = []string{"Formato desconocido"}
	}
	emitJSON(map[string]any{"hash": h, "posibles": out})
}

// ---------- fortaleza ----------

type strengthOut struct {
	Puntuacion      int      `json:"puntuacion"`
	Nivel           string   `json:"nivel"`
	Recomendaciones []string `json:"recomendaciones"`
}

func passStrength(pw string) strengthOut {
	score := 0
	var fb []string
	if len(pw) >= 12 {
		score += 2
	} else if len(pw) >= 8 {
		score += 1
	} else {
		fb = append(fb, "Usa al menos 12 caracteres.")
	}
	has := func(pat string) bool { ok, _ := regexp.MatchString(pat, pw); return ok }
	if has("[a-z]") && has("[A-Z]") {
		score++
	} else {
		fb = append(fb, "Mezcla mayúsculas y minúsculas.")
	}
	if has(`\d`) {
		score++
	} else {
		fb = append(fb, "Agrega números.")
	}
	if has(`[^A-Za-z0-9]`) {
		score++
	} else {
		fb = append(fb, "Agrega símbolos.")
	}
	uniq := map[rune]bool{}
	for _, r := range pw {
		uniq[r] = true
	}
	if len(pw) > 0 && float64(len(uniq)) < float64(len(pw))*0.6 {
		fb = append(fb, "Evita caracteres repetidos.")
	} else {
		score++
	}
	var nivel string
	switch {
	case score <= 2:
		nivel = "Muy débil"
	case score <= 3:
		nivel = "Débil"
	case score <= 4:
		nivel = "Aceptable"
	case score <= 5:
		nivel = "Fuerte"
	default:
		nivel = "Muy fuerte"
	}
	if fb == nil {
		fb = []string{}
	}
	return strengthOut{score, nivel, fb}
}

func cmdPass(args []string) {
	fs := flag.NewFlagSet("pass", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go pass <contraseña>")
		os.Exit(2)
	}
	emitJSON(passStrength(fs.Arg(0)))
}

// ---------- generador ----------

func cmdGenPass(args []string) {
	fs := flag.NewFlagSet("genpass", flag.ExitOnError)
	n := fs.Int("n", 16, "longitud 8-64")
	fs.Parse(args)
	if *n < 8 || *n > 64 {
		fmt.Fprintln(os.Stderr, "La longitud debe ser 8-64")
		os.Exit(2)
	}
	const abc = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
	var sb strings.Builder
	for i := 0; i < *n; i++ {
		j, err := rand.Int(rand.Reader, big.NewInt(int64(len(abc))))
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		sb.WriteByte(abc[j.Int64()])
	}
	pw := sb.String()
	b, err := breachCore(pw)
	out := map[string]any{"password": pw}
	if err != nil {
		out["brecha_error"] = err.Error()
	} else {
		out["filtrada"] = b > 0
		out["veces_vista"] = b
	}
	emitJSON(out)
}

// ---------- filtraciones HIBP (k-anonymity) ----------

var rangeCache = map[string]string{}
var rangeMu sync.Mutex
const maxRangeCache = 256

func fetchRange(prefix string) (string, error) {
	rangeMu.Lock()
	if body, ok := rangeCache[prefix]; ok {
		rangeMu.Unlock()
		return body, nil
	}
	rangeMu.Unlock()
	req, _ := http.NewRequest("GET", "https://api.pwnedpasswords.com/range/"+prefix, nil)
	req.Header.Set("User-Agent", "darkly-go/2.1 (educativo)")
	req.Header.Set("Add-Padding", "true")
	resp, err := httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	buf := make([]byte, 0, 65536)
	tmp := make([]byte, 4096)
	for {
		n, err := resp.Body.Read(tmp)
		if n > 0 {
			buf = append(buf, tmp[:n]...)
		}
		if err != nil || len(buf) > 200000 {
			break
		}
	}
	body := string(buf)
	rangeMu.Lock()
	if len(rangeCache) >= maxRangeCache {
		for k := range rangeCache {
			delete(rangeCache, k)
			break
		}
	}
	rangeCache[prefix] = body
	rangeMu.Unlock()
	return body, nil
}

func breachCore(pw string) (int, error) {
	sum := sha1.Sum([]byte(pw))
	hexsum := strings.ToUpper(hex.EncodeToString(sum[:]))
	prefix, suffix := hexsum[:5], hexsum[5:]
	body, err := fetchRange(prefix)
	if err != nil {
		return 0, err
	}
	for _, line := range strings.Split(body, "\n") {
		parts := strings.SplitN(strings.TrimSpace(line), ":", 2)
		if len(parts) != 2 {
			continue
		}
		if strings.ToUpper(parts[0]) == suffix {
			var n int
			fmt.Sscanf(parts[1], "%d", &n)
			return n, nil
		}
	}
	return 0, nil
}

func cmdBreach(args []string) {
	fs := flag.NewFlagSet("breach", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go breach <contraseña>")
		os.Exit(2)
	}
	n, err := breachCore(fs.Arg(0))
	if err != nil {
		emitJSON(map[string]string{"error": "No se pudo consultar HIBP: " + err.Error()})
		os.Exit(1)
	}
	out := map[string]any{"comprometida": n > 0, "veces_vista": n}
	if n > 0 {
		out["resultado"] = fmt.Sprintf("COMPROMETIDA: vista %d veces. Cámbiala ya.", n)
	} else {
		out["resultado"] = "No aparece en filtraciones conocidas."
	}
	emitJSON(out)
}

func cmdAudit(args []string) {
	fs := flag.NewFlagSet("audit", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go audit <contraseña>")
		os.Exit(2)
	}
	pw := fs.Arg(0)
	fuerza := passStrength(pw)
	n, err := breachCore(pw)
	var veredicto string
	switch {
	case err != nil:
		veredicto = fmt.Sprintf("Fortaleza %s; filtración no verificable (%v)", fuerza.Nivel, err)
	case n > 0:
		veredicto = fmt.Sprintf("NO USAR: filtrada %d veces aunque su fortaleza sea %s.", n, fuerza.Nivel)
	case fuerza.Nivel == "Fuerte" || fuerza.Nivel == "Muy fuerte":
		veredicto = "OK: fuerte y sin filtraciones conocidas."
	default:
		veredicto = fmt.Sprintf("Mejorable: %s y sin filtraciones, pero hazla más larga/única.", fuerza.Nivel)
	}
	emitJSON(map[string]any{
		"fortaleza":  fuerza,
		"veces_vista": n,
		"veredicto":  veredicto,
	})
}

// ---------- cabeceras ----------

func headersCore(rawurl string) map[string]any {
	rawurl = strings.TrimSpace(rawurl)
	if rawurl == "" {
		return map[string]any{"error": "URL vacía"}
	}
	var toTry []string
	if strings.HasPrefix(rawurl, "http://") || strings.HasPrefix(rawurl, "https://") {
		toTry = append(toTry, rawurl)
	} else {
		toTry = append(toTry, "https://"+rawurl, "http://"+rawurl)
	}
	for _, target := range toTry {
		for _, method := range []string{"HEAD", "GET"} {
			req, _ := http.NewRequest(method, target, nil)
			req.Header.Set("User-Agent", "darkly-go/2.1 (educativo)")
			resp, err := httpClient.Do(req)
			if err != nil {
				continue
			}
			out := map[string]any{}
			for k, v := range resp.Header {
				out[k] = strings.Join(v, "; ")
			}
			out["_url_final"] = resp.Request.URL.String()
			out["_metodo"] = method
			resp.Body.Close()
			return out
		}
	}
	return map[string]any{"error": "No se pudo obtener cabeceras. Verifica el host o tu conexión."}
}

func cmdHeaders(args []string) {
	fs := flag.NewFlagSet("headers", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go headers <url>")
		os.Exit(2)
	}
	emitJSON(headersCore(fs.Arg(0)))
}

// ---------- urlscan ----------

var susTLDs = map[string]bool{"tk": true, "ml": true, "ga": true, "cf": true, "gq": true, "zip": true, "mov": true, "click": true, "link": true}
var susWords = []string{"login", "verify", "secure", "account", "update", "free", "prize", "winner", "paypal", "bank", "gift"}

func cmdURLScan(args []string) {
	fs := flag.NewFlagSet("urlscan", flag.ExitOnError)
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go urlscan <url>")
		os.Exit(2)
	}
	original := strings.TrimSpace(fs.Arg(0))
	if !strings.Contains(original, "://") {
		original = "http://" + original
	}
	u, err := url.Parse(original)
	if err != nil {
		fmt.Fprintln(os.Stderr, "URL no válida:", err)
		os.Exit(2)
	}
	host := strings.TrimRight(strings.ToLower(u.Hostname()), ".")
	if host == "" {
		emitJSON(map[string]any{"url": original, "riesgo": 100, "nivel": "Alto", "hallazgos": []string{"No se encontró un host válido"}})
		return
	}
	var findings []string
	risk := 0
	if u.User != nil {
		findings = append(findings, "'@' en la autoridad — posible truco de redirección")
		risk += 25
	}
	if u.Scheme == "http" {
		findings = append(findings, "Usa HTTP sin cifrado (sin TLS)")
		risk += 10
	}
	if ip := strings.Trim(host, "[]"); net.ParseIP(ip) != nil {
		findings = append(findings, "El host es una IP cruda, no un dominio")
		risk += 20
	}
	if strings.HasPrefix(host, "xn--") || strings.Contains(host, "xn--") {
		findings = append(findings, "Punycode (xn--) — posible suplantación homógrafa/IDN")
		risk += 20
	}
	parts := strings.Split(strings.Trim(host, "[]"), ".")
	if len(parts) > 4 {
		findings = append(findings, fmt.Sprintf("Muchos subdominios (%d) — posible suplantación", len(parts)))
		risk += 10
	}
	if len(parts) > 0 && susTLDs[parts[len(parts)-1]] {
		findings = append(findings, "TLD sospechoso: ."+parts[len(parts)-1])
		risk += 15
	}
	low := strings.ToLower(original)
	mainDomain := host
	if len(parts) >= 2 {
		mainDomain = strings.Join(parts[len(parts)-2:], ".")
	}
	for _, w := range susWords {
		if strings.Contains(low, w) {
			if (w == "paypal" || w == "bank") && (mainDomain == w+".com" || strings.HasSuffix(mainDomain, "."+w+".com") || strings.HasPrefix(mainDomain, w+".")) {
				continue
			}
			findings = append(findings, "Palabra '"+w+"' muy usada en phishing")
			risk += 5
			break
		}
	}
	if len(original) > 150 {
		findings = append(findings, "URL muy larga — suele usarse para ocultar el host real")
		risk += 10
	}
	if u.Port() != "" && u.Port() != "80" && u.Port() != "443" {
		findings = append(findings, "Puerto inusual: "+u.Port())
		risk += 10
	}
	if risk > 100 {
		risk = 100
	}
	nivel := "Bajo"
	if risk >= 60 {
		nivel = "Alto"
	} else if risk >= 30 {
		nivel = "Medio"
	}
	if findings == nil {
		findings = []string{"Sin señales obvias (igual verifica el remitente/contexto)"}
	}
	emitJSON(map[string]any{"url": original, "host": host, "esquema": u.Scheme, "riesgo": risk, "nivel": nivel, "hallazgos": findings})
}
