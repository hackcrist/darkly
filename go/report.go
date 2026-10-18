// report.go: informe 10/10 por IP en HTML+TXT+CSV+PDF.
package main

import (
	"crypto/sha256"
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"html"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

func safeName(s string) string {
	re := regexp.MustCompile(`[^A-Za-z0-9.\-_]+`)
	s = re.ReplaceAllString(s, "_")
	s = strings.Trim(s, "_")
	if s == "" {
		s = "reporte"
	}
	return s
}

func kvTable(m map[string]any) string {
	if len(m) == 0 {
		return "<p>Sin datos.</p>"
	}
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var sb strings.Builder
	sb.WriteString("<table>")
	for _, k := range keys {
		sb.WriteString("<tr><th>" + html.EscapeString(k) + "</th><td>" + html.EscapeString(fmt.Sprintf("%v", m[k])) + "</td></tr>")
	}
	sb.WriteString("</table>")
	return sb.String()
}

func cmdReport(args []string) {
	fs := flag.NewFlagSet("report", flag.ExitOnError)
	ipFlag := fs.String("ip", "", "IP a reportar (requerido)")
	objetivo := fs.String("objetivo", "", "dominio original o etiqueta")
	nombre := fs.String("nombre", "", "nombre específico del reporte")
	outdir := fs.String("outdir", "", "carpeta de salida (defecto: ../reportes)")
	fs.Parse(args)
	if *ipFlag == "" {
		fmt.Fprintln(os.Stderr, "uso: darkly-go report --ip 8.8.8.8 [--objetivo google.com] [--nombre casa]")
		os.Exit(2)
	}
	ip := strings.TrimSpace(*ipFlag)
	obj := *objetivo
	if obj == "" {
		obj = ip
	}
	etag := safeName(*nombre)
	if *nombre == "" {
		etag = safeName(ip)
	}
	dir := *outdir
	if dir == "" {
		exe, _ := os.Executable()
		dir = filepath.Join(filepath.Dir(exe), "..", "reportes")
		if _, err := os.Stat(dir); err != nil {
			dir = "reportes"
		}
	}
	os.MkdirAll(dir, 0755)
	ts := time.Now().Format("20060102_150405")
	fecha := time.Now().Format("2006-01-02 15:04:05")
	fechaUTC := time.Now().UTC().Format("2006-01-02 15:04:05 UTC")
	tag := etag + "_" + ts

	geo := geoCore(ip)
	ptr := ptrCore(ip)
	rdap := rdapCore(ip)
	dns := dnsCore(obj)
	ping := pingCore(ip)
	ports := map[string]string{}
	if plist, err := parsePorts("22,80,443,8080,3389"); err == nil {
		if _, res := scanCore(ip, plist, 1000, 50); res["error"] == nil {
			for k, v := range res {
				if open, _ := v["open"].(bool); open {
					ports[k] = fmt.Sprintf("%v", v["banner"])
				} else {
					ports[k] = "cerrado"
				}
			}
		}
	}
	headers := headersCore("https://" + ip)

	// Resumen
	ciudad, pais, org := "?", "?", "?"
	if v, ok := geo["city"]; ok {
		ciudad = fmt.Sprintf("%v", v)
	}
	if v, ok := geo["country"]; ok {
		pais = fmt.Sprintf("%v", v)
	}
	if v, ok := geo["org"]; ok {
		org = fmt.Sprintf("%v", v)
	}
	mapa := "Sin coordenadas"
	if lat, ok1 := geo["lat"]; ok1 {
		if lon, ok2 := geo["lon"]; ok2 {
			mapa = fmt.Sprintf("https://www.google.com/maps?q=%v,%v", lat, lon)
		}
	}

	// ---------- Evidencia JSON + integridad (SHA-256 del propio archivo) ----------
	geoVerif, _ := geo["verificacion"].(map[string]any)
	evidencia := map[string]any{
		"herramienta":    "Darkly-Go",
		"generado_local": fecha,
		"generado_utc":   fechaUTC,
		"ip":             ip,
		"objetivo":       obj,
		"nombre":         etag,
		"geo":            geo,
		"ptr":            ptr,
		"rdap":           rdap,
		"dns":            dns,
		"ping":           ping,
		"puertos":        ports,
		"cabeceras":      headers,
	}
	evBytes, _ := json.MarshalIndent(evidencia, "", "  ")
	sum := sha256.Sum256(evBytes)
	sha := fmt.Sprintf("%x", sum)
	jsonPath := filepath.Join(dir, "reporte_IP_"+tag+".json")
	os.WriteFile(jsonPath, evBytes, 0644)

	// ---------- TXT ----------
	txtPath := filepath.Join(dir, "reporte_IP_"+tag+".txt")
	var tb strings.Builder
	bar := strings.Repeat("=", 60) + "\n"
	sec := func(t, cuerpo string) {
		tb.WriteString(strings.Repeat("-", 60) + "\n" + t + "\n" + strings.Repeat("-", 60) + "\n" + cuerpo + "\n")
	}
	tb.WriteString(bar + " DARKLY-GO - INFORME DETALLADO POR IP (10/10)\n Solo fines educativos.\n" + bar)
	tb.WriteString(fmt.Sprintf("Fecha: %s\nGenerado UTC: %s\nIP analizada: %s\nObjetivo original: %s\nNombre reporte: %s\n", fecha, fechaUTC, ip, obj, etag))
	tb.WriteString(fmt.Sprintf("Evidencia JSON: reporte_IP_%s.json\nSHA-256 (evidencia): %s\n\n", tag, sha))
	sec("[1] GEOLOCALIZACION / PROVEEDOR", kvTextOmit(geo, "verificacion"))
	sec("[2] DNS INVERSO (PTR)", ptr)
	sec("[3] RDAP - REGISTRO PRECISO", kvText(rdap))
	sec("[4] DNS DIRECTO / RESOLUCION", kvText(dns))
	ping = truncStr(ping, 1500)
	sec("[5] PING / LATENCIA", ping)
	var pb strings.Builder
	pkeys := make([]string, 0, len(ports))
	for k := range ports {
		pkeys = append(pkeys, k)
	}
	sort.Slice(pkeys, func(i, j int) bool {
		ai, _ := strconv.Atoi(pkeys[i])
		aj, _ := strconv.Atoi(pkeys[j])
		return ai < aj
	})
	for _, k := range pkeys {
		fmt.Fprintf(&pb, "puerto %-5s %-15s: %s\n", k, serviceOf(k, ports[k]), ports[k])
	}
	sec("[6] TOP PUERTOS + BANNERS", pb.String())
	sec("[7] CABECERAS HTTP", kvText(headers))
	if geoVerif != nil {
		vb := fmt.Sprintf("fuentes_ok: %v | fuentes_error: %v\ncoincide_pais: %v | coincide_asn: %v\n",
			geoVerif["fuentes_ok"], geoVerif["fuentes_error"], geoVerif["coincide_pais"], geoVerif["coincide_asn"])
		if avisos, ok := geoVerif["avisos"].([]string); ok {
			if len(avisos) == 0 {
				vb += "Avisos: ninguno\n"
			} else {
				vb += "Avisos: " + strings.Join(avisos, " | ") + "\n"
			}
		}
		if det, ok := geoVerif["detalle"].([]map[string]any); ok {
			for _, dm := range det {
				vb += fmt.Sprintf("  - %v: %v / %v / %v\n", dm["fuente"], dm["pais"], dm["org"], dm["asn"])
			}
		}
		sec("[8] VERIFICACION MULTI-FUENTE", vb)
	}
	sec("[9] EVIDENCIA E INTEGRIDAD", fmt.Sprintf("Archivo JSON: reporte_IP_%s.json\nSHA-256: %s\nGenerado UTC: %s", tag, sha, fechaUTC))
	tb.WriteString(bar + "RESUMEN EJECUTIVO\n" + bar)
	tb.WriteString(fmt.Sprintf("IP %s (%s) -> %s, %s | Org: %s | PTR: %s\nMapa: %s\n", ip, obj, ciudad, pais, org, ptr, mapa))
	tb.WriteString(fmt.Sprintf("Archivos: reporte_IP_%s.txt + .html + .csv + .pdf + .json\nIntegridad SHA-256: %s\n", tag, sha))
	os.WriteFile(txtPath, []byte(tb.String()), 0644)

	// ---------- CSV ----------
	csvPath := filepath.Join(dir, "reporte_IP_"+tag+".csv")
	if cf, err := os.Create(csvPath); err == nil {
		cw := csv.NewWriter(cf)
		cw.Write([]string{"campo", "valor"})
		cw.Write([]string{"fecha", fecha})
		cw.Write([]string{"fecha_utc", fechaUTC})
		cw.Write([]string{"sha256_evidencia", sha})
		cw.Write([]string{"ip", ip})
		cw.Write([]string{"objetivo", obj})
		cw.Write([]string{"nombre", etag})
		for k, v := range geo {
			cw.Write([]string{"geo." + k, fmt.Sprintf("%v", v)})
		}
		cw.Write([]string{"ptr", ptr})
		for k, v := range rdap {
			cw.Write([]string{"rdap." + k, fmt.Sprintf("%v", v)})
		}
		for _, k := range pkeys {
			cw.Write([]string{"puerto." + k, serviceOf(k, ports[k]) + " | " + ports[k]})
		}
		cw.Flush()
		cf.Close()
	}

	// ---------- HTML ----------
	htmlPath := filepath.Join(dir, "reporte_IP_"+tag+".html")
	verifCard := ""
	if geoVerif != nil {
		var vb strings.Builder
		vb.WriteString(fmt.Sprintf("<p>Fuentes OK: <b>%v</b> | Error: <b>%v</b> | Acuerdo pais: <b>%v</b> | Acuerdo ASN: <b>%v</b></p><table>",
			geoVerif["fuentes_ok"], geoVerif["fuentes_error"], geoVerif["coincide_pais"], geoVerif["coincide_asn"]))
		if det, ok := geoVerif["detalle"].([]map[string]any); ok {
			for _, dm := range det {
				vb.WriteString("<tr><th>" + html.EscapeString(fmt.Sprintf("%v", dm["fuente"])) + "</th><td>" +
					html.EscapeString(fmt.Sprintf("%v", dm["pais"])) + " / " +
					html.EscapeString(fmt.Sprintf("%v", dm["org"])) + " / " +
					html.EscapeString(fmt.Sprintf("%v", dm["asn"])) + "</td></tr>")
			}
		}
		vb.WriteString("</table><ul>")
		if avisos, ok := geoVerif["avisos"].([]string); ok && len(avisos) > 0 {
			for _, a := range avisos {
				vb.WriteString("<li>" + html.EscapeString(a) + "</li>")
			}
		} else {
			vb.WriteString("<li>Sin discrepancias.</li>")
		}
		vb.WriteString("</ul>")
		verifCard = `<div class="card"><h2>8. Verificacion multi-fuente</h2>` + vb.String() + `</div>`
	}
	evidCard := `<div class="card"><h2>9. Evidencia e integridad</h2><p>Generado (UTC): <b>` +
		html.EscapeString(fechaUTC) + `</b></p><p>Evidencia JSON: <b>reporte_IP_` + html.EscapeString(tag) +
		`.json</b></p><p>SHA-256: <code>` + html.EscapeString(sha) + `</code></p></div>`
	var hb strings.Builder
	hb.WriteString(`<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Darkly-Go - Informe IP ` + html.EscapeString(ip) + `</title>
<style>*{box-sizing:border-box}body{margin:0;font-family:'Segoe UI',Arial,sans-serif;background:#0a0a14;color:#e8e8f0}
header{padding:40px 20px;text-align:center;background:linear-gradient(135deg,#00ffea,#b026ff,#ff00ff);color:#000}
header h1{margin:0;font-size:2.2em;letter-spacing:2px}header p{margin:8px 0 0;font-weight:bold}
.wrap{max-width:900px;margin:-20px auto 40px;padding:0 16px}
.card{background:#14142b;border:1px solid #2de2ff55;border-radius:14px;padding:20px;margin:16px 0}
.card h2{margin-top:0;color:#00ffea}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #ffffff18}
th{color:#00ffea;width:35%}td{color:#fff}.badge{display:inline-block;background:linear-gradient(90deg,#00ffea,#ff00ff);color:#000;font-weight:bold;border-radius:20px;padding:6px 18px;margin:4px}
footer{text-align:center;color:#888;padding:20px;font-size:.85em}a{color:#00ffea}pre{white-space:pre-wrap;color:#fff}</style></head><body>
<header><h1>DARKLY-GO</h1><p>Informe detallado por IP - ` + html.EscapeString(ip) + `</p>
<p style="font-size:.9em">` + html.EscapeString(fecha) + ` | UTC: ` + html.EscapeString(fechaUTC) + ` | Objetivo: ` + html.EscapeString(obj) + ` | Nombre: ` + html.EscapeString(etag) + `</p></header>
<div class="wrap"><div class="card"><h2>Resumen</h2>
<span class="badge">IP: ` + html.EscapeString(ip) + `</span>
<span class="badge">PTR: ` + html.EscapeString(truncStr(ptr, 60)) + `</span>
<p>Ciudad: <b>` + html.EscapeString(ciudad) + `</b> | País: <b>` + html.EscapeString(pais) + `</b> | Org: <b>` + html.EscapeString(org) + `</b></p>
<p><a href="` + html.EscapeString(mapa) + `" target="_blank">Ver mapa</a></p></div>
<div class="card"><h2>1. Geolocalización</h2>` + kvTableOmit(geo, "verificacion") + `</div>
<div class="card"><h2>2. PTR</h2><p>` + html.EscapeString(ptr) + `</p></div>
<div class="card"><h2>3. RDAP</h2>` + kvTable(rdap) + `</div>
<div class="card"><h2>4. DNS directo</h2>` + kvTable(dns) + `</div>
<div class="card"><h2>5. Ping</h2><pre>` + html.EscapeString(truncStr(ping, 1500)) + `</pre></div>
<div class="card"><h2>6. Puertos</h2>` + portsTable(ports) + `</div>
<div class="card"><h2>7. Cabeceras HTTP</h2>` + kvTable(headers) + `</div>` + verifCard + evidCard + `
</div><footer>Darkly-Go (educativo) - Úsalo con responsabilidad y autorización.<br><a href="index.html">Ver todos los reportes</a></footer></body></html>`)
	os.WriteFile(htmlPath, []byte(hb.String()), 0644)

	// ---------- PDF mínimo ----------
	pdfPath := filepath.Join(dir, "reporte_IP_"+tag+".pdf")
	writeMiniPDF(pdfPath, []string{
		"DARKLY-GO - INFORME IP", "Fecha: " + fecha + " | IP: " + ip,
		"Generado UTC: " + fechaUTC,
		"Objetivo: " + obj + " | Nombre: " + etag, "",
		"Geo: " + ciudad + ", " + pais + " | Org: " + org,
		"PTR: " + truncStr(ptr, 90), "Mapa: " + mapa,
		"Evidencia: reporte_IP_" + tag + ".json", "SHA-256: " + sha,
	})

	updateIndexGo(dir)
	emitJSON(map[string]string{"html": htmlPath, "txt": txtPath, "csv": csvPath, "pdf": pdfPath, "json": jsonPath})
}

// serviceOf deduce el servicio (estilo nmap) de un puerto y su detalle.
func serviceOf(portKey, detalle string) string {
	p, _ := strconv.Atoi(portKey)
	banner := ""
	if detalle != "cerrado" {
		banner = detalle
	}
	return serviceName(p, banner)
}

// kvTextOmit formatea un mapa como texto omitiendo claves concretas.
func kvTextOmit(m map[string]any, omit ...string) string {
	skip := make(map[string]bool, len(omit))
	for _, k := range omit {
		skip[k] = true
	}
	filtered := map[string]any{}
	for k, v := range m {
		if !skip[k] {
			filtered[k] = v
		}
	}
	return kvText(filtered)
}

// kvTableOmit formatea un mapa como tabla HTML omitiendo claves concretas.
func kvTableOmit(m map[string]any, omit ...string) string {
	skip := make(map[string]bool, len(omit))
	for _, k := range omit {
		skip[k] = true
	}
	filtered := map[string]any{}
	for k, v := range m {
		if !skip[k] {
			filtered[k] = v
		}
	}
	return kvTable(filtered)
}

func kvText(m map[string]any) string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var sb strings.Builder
	for _, k := range keys {
		fmt.Fprintf(&sb, "%15s : %v\n", k, m[k])
	}
	return sb.String()
}

func truncStr(s string, n int) string {
	if len(s) <= n {
		return s
	}
	// Recorta por runas para no partir caracteres UTF-8 (tildes, etc.).
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n])
}

func portsTable(ports map[string]string) string {
	if len(ports) == 0 {
		return "<p>Sin datos.</p>"
	}
	keys := make([]string, 0, len(ports))
	for k := range ports {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var sb strings.Builder
	sb.WriteString("<table><tr><th>PORT</th><th>SERVICE</th><th>DETALLE</th></tr>")
	for _, k := range keys {
		sb.WriteString("<tr><th>" + html.EscapeString(k) + "</th><td>" + html.EscapeString(serviceOf(k, ports[k])) + "</td><td>" + html.EscapeString(ports[k]) + "</td></tr>")
	}
	sb.WriteString("</table>")
	return sb.String()
}

func writeMiniPDF(path string, lines []string) {
	var clean []string
	for _, ln := range lines {
		if len(clean) >= 80 {
			break
		}
		var sb strings.Builder
		for _, r := range ln {
			if r < 128 {
				sb.WriteRune(r)
			} else {
				sb.WriteRune('?')
			}
		}
		clean = append(clean, sb.String())
	}
	content := "BT /F1 11 Tf 40 780 Td 14 TL "
	for _, ln := range clean {
		esc := strings.ReplaceAll(strings.ReplaceAll(ln, "\\", "\\\\"), "(", "\\(")
		esc = strings.ReplaceAll(esc, ")", "\\)")
		content += "(" + esc + ") Tj T* "
	}
	content += "ET"
	objs := []string{
		"<< /Type /Catalog /Pages 2 0 R >>",
		"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
		"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
		"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
		fmt.Sprintf("<< /Length %d >>\nstream\n%s\nendstream", len(content), content),
	}
	var out strings.Builder
	out.WriteString("%PDF-1.4\n")
	offsets := []int{0}
	for i, body := range objs {
		offsets = append(offsets, out.Len())
		fmt.Fprintf(&out, "%d 0 obj\n%s\nendobj\n", i+1, body)
	}
	xref := out.Len()
	fmt.Fprintf(&out, "xref\n0 %d\n0000000000 65535 f \n", len(objs)+1)
	for _, off := range offsets[1:] {
		fmt.Fprintf(&out, "%010d 00000 n \n", off)
	}
	fmt.Fprintf(&out, "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF", len(objs)+1, xref)
	os.WriteFile(path, []byte(out.String()), 0644)
}

func updateIndexGo(dir string) {
	entries, _ := os.ReadDir(dir)
	var items []string
	for _, e := range entries {
		n := e.Name()
		if strings.HasPrefix(n, "reporte_IP_") && strings.HasSuffix(n, ".html") && n != "index.html" {
			items = append(items, `<li><a href="`+html.EscapeString(n)+`">`+html.EscapeString(n)+`</a></li>`)
		}
	}
	sort.Sort(sort.Reverse(sort.StringSlice(items)))
	body := strings.Join(items, "")
	if body == "" {
		body = "<li>Sin reportes aún.</li>"
	}
	page := `<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Darkly-Go - Reportes</title>
<style>body{font-family:Segoe UI,Arial;background:#0a0a14;color:#eee;margin:0}
header{padding:30px;text-align:center;background:linear-gradient(135deg,#00ffea,#ff00ff)}
h1{margin:0;color:#000}ul{max-width:700px;margin:20px auto;list-style:none;padding:0}
li{background:#14142b;margin:8px;padding:12px 16px;border-radius:10px;border:1px solid #2de2ff44}
a{color:#00ffea;text-decoration:none;font-weight:bold}</style></head>
<body><header><h1>DARKLY-GO - REPORTES POR IP</h1></header><ul>` + body + `</ul></body></html>`
	os.WriteFile(filepath.Join(dir, "index.html"), []byte(page), 0644)
}
