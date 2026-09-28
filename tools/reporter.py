"""Generador de reportes detallados (HTML + TXT + CSV + PDF) en carpeta reportes/."""
import os
import csv
import html
import datetime


BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reportes")


def ensure_dir() -> str:
    os.makedirs(BASE_DIR, exist_ok=True)
    return BASE_DIR


def _stamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in name).strip("_") or "reporte"


def _kv_table(data: dict) -> str:
    rows = []
    for k, v in (data or {}).items():
        rows.append(f"<tr><th>{html.escape(str(k))}</th><td>{html.escape(str(v))}</td></tr>")
    return "<table>" + "".join(rows) + "</table>" if rows else "<p>Sin datos.</p>"


def build_ip_report(ip: str, geo: dict, ptr: str, rdap: dict, nombre: str | None = None, objetivo: str = "", extra: dict | None = None) -> tuple[str, str, str, str]:
    """Reporte 10/10: geo + PTR + RDAP + extra(dns, ping, puertos, headers, notas).
    nombre: etiqueta específica. objetivo: input original."""
    ensure_dir()
    ts = _stamp()
    etiqueta = _safe(nombre) if nombre else _safe(ip)
    tag = f"{etiqueta}_{ts}"
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    extra = extra or {}
    dns_d = extra.get("dns", "")
    ping_d = extra.get("ping", "")
    puertos_d = extra.get("puertos", {})
    headers_d = extra.get("headers", {})
    notas_d = extra.get("notas", "")

    def _sec(t: str, cuerpo: str) -> str:
        return f"{'-' * 60}\n{t}\n{'-' * 60}\n{cuerpo}\n"

    # ---------- TXT detallado ----------
    txt_path = os.path.join(BASE_DIR, f"reporte_IP_{tag}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(" DARKLY TOOLS - INFORME DETALLADO POR IP (10/10)\n")
        f.write(" Solo fines educativos. Uso responsable y autorizado.\n")
        f.write("=" * 60 + "\n")
        f.write(f"Fecha: {fecha}\nIP analizada: {ip}\n")
        if objetivo:
            f.write(f"Objetivo original: {objetivo}\n")
        if nombre:
            f.write(f"Nombre reporte: {nombre}\n")
        f.write(f"Metodo: geo multi-fuente + PTR + RDAP HTTPS + ping + top-puertos + headers\n\n")
        gtxt = "\n".join(f"{k:>15} : {v}" for k, v in (geo.items() if isinstance(geo, dict) else {"dato": geo}.items()))
        f.write(_sec("[1] GEOLOCALIZACION / PROVEEDOR", gtxt))
        f.write(_sec("[2] DNS INVERSO (PTR)", str(ptr)))
        rtxt = "\n".join(f"{k:>15} : {v}" for k, v in (rdap.items() if isinstance(rdap, dict) else {"dato": rdap}.items()))
        f.write(_sec("[3] RDAP - REGISTRO PRECISO", rtxt))
        f.write(_sec("[4] DNS DIRECTO / RESOLUCION", str(dns_d) if dns_d else "No recolectado (informe rapido)"))
        f.write(_sec("[5] PING / LATENCIA", str(ping_d)[:1500] if ping_d else "No recolectado (informe rapido)"))
        if puertos_d:
            ptxt = "\n".join(f"puerto {p:<5}: {v}" for p, v in sorted(puertos_d.items(), key=lambda kv: str(kv[0])))
        else:
            ptxt = "No recolectado (informe rapido). Usa opcion 5 para top-puertos."
        f.write(_sec("[6] TOP PUERTOS + BANNERS", ptxt))
        if headers_d and isinstance(headers_d, dict) and "error" not in headers_d:
            htxt = "\n".join(f"{k:>20} : {v}" for k, v in headers_d.items())
        else:
            htxt = str(headers_d) if headers_d else "No recolectado o sin HTTP."
        f.write(_sec("[7] CABECERAS HTTP", htxt[:2000]))
        if notas_d:
            f.write(_sec("[8] NOTAS", str(notas_d)))
        pais = geo.get("country", "?") if isinstance(geo, dict) else "?"
        ciudad = geo.get("city", "?") if isinstance(geo, dict) else "?"
        org = geo.get("org", "?") if isinstance(geo, dict) else "?"
        lat, lon = (geo.get("lat"), geo.get("lon")) if isinstance(geo, dict) else (None, None)
        mapa = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else "Sin coordenadas"
        f.write("=" * 60 + "\nRESUMEN EJECUTIVO\n" + "=" * 60 + "\n")
        f.write(f"IP {ip} ({objetivo or ip}) -> {ciudad}, {pais} | Org: {org} | PTR: {ptr}\n")
        f.write(f"Mapa: {mapa}\nArchivos: {os.path.basename(txt_path)} + .html gemelo\n")

    # ---------- HTML super mejor 10/10 ----------
    html_path = os.path.join(BASE_DIR, f"reporte_IP_{tag}.html")
    geo_h = _kv_table(geo if isinstance(geo, dict) else {"dato": geo})
    rdap_h = _kv_table(rdap if isinstance(rdap, dict) else {"dato": rdap})
    dns_h = _kv_table(dns_d if isinstance(dns_d, dict) else {"resultado": str(dns_d)[:500]}) if dns_d else "<p>No recolectado (informe rápido).</p>"
    if puertos_d:
        rows_p = "".join(f"<tr><th>puerto {html.escape(str(p))}</th><td>{html.escape(str(v))}</td></tr>" for p, v in sorted(puertos_d.items(), key=lambda kv: str(kv[0])))
        puertos_h = "<table>" + rows_p + "</table>"
    else:
        puertos_h = "<p>No recolectado (informe rápido). Usa opción 5 informe completo.</p>"
    if headers_d and isinstance(headers_d, dict) and "error" not in headers_d:
        headers_h = _kv_table(headers_d)
    else:
        headers_h = f"<p>{html.escape(str(headers_d)[:500]) if headers_d else 'Sin HTTP.'}</p>"
    lat, lon = (geo.get("lat"), geo.get("lon")) if isinstance(geo, dict) else (None, None)
    if lat and lon:
        mapa_h = f'<p><a href="https://www.google.com/maps?q={lat},{lon}" target="_blank">Ver en Google Maps ({lat},{lon})</a></p><iframe width="100%" height="300" style="border:0;border-radius:10px" src="https://www.openstreetmap.org/export/embed.html?bbox={lon-1}%2C{lat-1}%2C{lon+1}%2C{lat+1}&layer=mapnik&marker={lat}%2C{lon}"></iframe>'
    else:
        mapa_h = "<p>Sin coordenadas.</p>"
    ping_h = f"<pre>{html.escape(str(ping_d)[:1500])}</pre>" if ping_d else "<p>No recolectado (informe rápido).</p>"
    pagina = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Darkly Tools - Informe IP {html.escape(ip)}</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;font-family:'Segoe UI',Arial,sans-serif;background:#0a0a14;color:#e8e8f0}}
header{{padding:40px 20px;text-align:center;background:linear-gradient(135deg,#00ffea,#b026ff,#ff00ff);color:#000}}
header h1{{margin:0;font-size:2.2em;letter-spacing:2px;text-shadow:0 0 20px #fff}}
header p{{margin:8px 0 0;font-weight:bold}}
.wrap{{max-width:900px;margin:-20px auto 40px;padding:0 16px}}
.card{{background:#14142b;border:1px solid #2de2ff55;border-radius:14px;padding:20px;margin:16px 0;box-shadow:0 0 25px #00ffea22}}
.card h2{{margin-top:0;color:#00ffea;text-shadow:0 0 12px #00ffea}}
.card h2.v{{color:#c26bff;text-shadow:0 0 12px #b026ff}}
.card h2.y{{color:#ffe600;text-shadow:0 0 12px #ffe600}}
table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid #ffffff18}}
th{{color:#00ffea;width:35%}}td{{color:#fff}}
.badge{{display:inline-block;background:linear-gradient(90deg,#00ffea,#ff00ff);color:#000;font-weight:bold;border-radius:20px;padding:6px 18px;margin:4px}}
footer{{text-align:center;color:#888;padding:20px;font-size:.85em}}
a{{color:#00ffea}}
</style></head><body>
<header><h1>DARKLY TOOLS</h1><p>Informe detallado por IP - {html.escape(ip)}</p>
<p style="font-size:.9em">{html.escape(fecha)} | Solo fines educativos</p>
{f'<p style="font-size:.9em">Objetivo: {html.escape(objetivo)} | Nombre: {html.escape(nombre or "")}</p>' if (objetivo or nombre) else ''}</header>
<div class="wrap">
<div class="card"><h2>Resumen</h2>
<span class="badge">IP: {html.escape(ip)}</span>
<span class="badge">PTR: {html.escape(str(ptr))[:60]}</span>
<p>Ciudad: <b>{html.escape(str((geo or {{}}).get('city','?') if isinstance(geo,dict) else '?'))}</b> |
País: <b>{html.escape(str((geo or {{}}).get('country','?') if isinstance(geo,dict) else '?'))}</b> |
Org: <b>{html.escape(str((geo or {{}}).get('org','?') if isinstance(geo,dict) else '?'))}</b></p>{mapa_h}</div>
<div class="card"><h2>1. Geolocalización / Proveedor</h2>{geo_h}</div>
<div class="card"><h2 class="v">2. DNS inverso (PTR)</h2><p>{html.escape(str(ptr))}</p></div>
<div class="card"><h2 class="y">3. RDAP - Registro preciso</h2>{rdap_h}</div>
<div class="card"><h2>4. DNS directo</h2>{dns_h}</div>
<div class="card"><h2 class="v">5. Ping / Latencia</h2>{ping_h}</div>
<div class="card"><h2 class="y">6. Top puertos + banners</h2>{puertos_h}</div>
<div class="card"><h2>7. Cabeceras HTTP</h2>{headers_h}</div>
<div class="card"><h2 class="v">8. Metodología</h2><p>Geo multi-fuente + PTR + RDAP HTTPS + ping + top-puertos con banner + headers. Solo pasivo/defensivo, sin exploits. Uso educativo autorizado.</p></div>
</div>
<footer>Darkly Tools (educativo) - Úsalo con responsabilidad y autorización.<br>
<a href="index.html">Ver todos los reportes</a></footer>
</body></html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(pagina)

    _update_index()
    csv_path = _export_csv(tag, fecha, ip, objetivo, nombre or "", geo, ptr, rdap, puertos_d, headers_d)
    pdf_path = _export_pdf(tag, fecha, ip, objetivo, nombre or "", geo, ptr, rdap, puertos_d)
    return html_path, txt_path, csv_path, pdf_path


def _export_csv(tag: str, fecha: str, ip: str, objetivo: str, nombre: str, geo: dict, ptr: str, rdap: dict, puertos: dict, headers: dict) -> str:
    path = os.path.join(BASE_DIR, f"reporte_IP_{tag}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["campo", "valor"])
        w.writerow(["fecha", fecha])
        w.writerow(["ip", ip])
        w.writerow(["objetivo", objetivo])
        w.writerow(["nombre", nombre])
        if isinstance(geo, dict):
            for k, v in geo.items():
                w.writerow([f"geo.{k}", v])
        w.writerow(["ptr", ptr])
        if isinstance(rdap, dict):
            for k, v in rdap.items():
                w.writerow([f"rdap.{k}", v])
        if isinstance(puertos, dict):
            for p, v in puertos.items():
                w.writerow([f"puerto.{p}", v])
        if isinstance(headers, dict) and "error" not in headers:
            for k, v in list(headers.items())[:20]:
                w.writerow([f"header.{k}", str(v)[:200]])
    return path


def _export_pdf(tag: str, fecha: str, ip: str, objetivo: str, nombre: str, geo: dict, ptr: str, rdap: dict, puertos: dict) -> str:
    """PDF mínimo válido sin dependencias (texto plano, Helvetica)."""
    path = os.path.join(BASE_DIR, f"reporte_IP_{tag}.pdf")
    lines = [
        "DARKLY TOOLS - INFORME IP",
        f"Fecha: {fecha} | IP: {ip}",
        f"Objetivo: {objetivo or ip} | Nombre: {nombre or '-'}",
        "",
        "[1] GEO/PROVEEDOR",
    ]
    if isinstance(geo, dict):
        for k, v in geo.items():
            lines.append(f"{k}: {v}")
    lines += ["", "[2] PTR", str(ptr), "", "[3] RDAP"]
    if isinstance(rdap, dict):
        for k, v in rdap.items():
            lines.append(f"{k}: {v}")
    lines += ["", "[4] PUERTOS"]
    if puertos:
        for p, v in puertos.items():
            lines.append(f"puerto {p}: {v}")
    else:
        lines.append("No recolectado (informe rapido)")
    lines += ["", "Solo fines educativos. Uso responsable y autorizado."]
    # Limpia a latin-1 seguro
    clean = []
    for ln in lines[:80]:
        clean.append(ln.encode("latin-1", errors="replace").decode("latin-1"))
    # Contenido PDF
    content = "BT /F1 11 Tf 40 780 Td 14 TL "
    for ln in clean:
        esc = ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content += f"({esc}) Tj T* "
    content += "ET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode("latin-1")
    for off in offsets[1:]:
        out += f"{off:010d} 00000 n \n".encode("latin-1")
    out += f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode("latin-1")
    with open(path, "wb") as f:
        f.write(out)
    return path


def _update_index():
    ensure_dir()
    idx = os.path.join(BASE_DIR, "index.html")
    archivos = sorted([a for a in os.listdir(BASE_DIR) if a.startswith("reporte_IP_") and a.endswith(".html")], reverse=True)
    items = "".join(f'<li><a href="{html.escape(a)}">{html.escape(a)}</a></li>' for a in archivos) or "<li>Sin reportes aún.</li>"
    pagina = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>Darkly Tools - Reportes</title>
<style>body{{font-family:Segoe UI,Arial;background:#0a0a14;color:#eee;margin:0}}
header{{padding:30px;text-align:center;background:linear-gradient(135deg,#00ffea,#ff00ff)}}
h1{{margin:0;color:#000}}ul{{max-width:700px;margin:20px auto;list-style:none;padding:0}}
li{{background:#14142b;margin:8px;padding:12px 16px;border-radius:10px;border:1px solid #2de2ff44}}
a{{color:#00ffea;text-decoration:none;font-weight:bold}}</style></head>
<body><header><h1>DARKLY - REPORTES POR IP</h1></header>
<ul>{items}</ul></body></html>"""
    with open(idx, "w", encoding="utf-8") as f:
        f.write(pagina)


def list_reports() -> list[str]:
    ensure_dir()
    return sorted(os.listdir(BASE_DIR), reverse=True)
