# Darkly Tools v2.0.0 | Herramientas de Linux y Seguridad

Colección educativa en español: redes, seguridad defensiva, recolección pasiva, sistema e info por IP. Con banner neón, menús con color y reportes HTML/TXT automáticos.

> Solo fines educativos. Úsalo con responsabilidad y autorización. El escaneo de puertos pide confirmación.

## Estructura

```
darkly-tools/
  darkly.py            # menú interactivo neón (español)
  tools/
    networking.py      # DNS con respaldo DoH, ping, port scan + banner grab, traceroute, subredes
    security.py        # hash, fortaleza/generador+verificado, cabeceras, URL, auditoría HIBP con caché
    gathering.py       # IP multi-fuente, headers HEAD+GET, PTR, WHOIS, RDAP, DNS records, subdominios, GitHub
    username.py        # búsqueda pasiva de usuario en 17 sitios públicos + reporte TXT
    system_tools.py    # sysinfo, disco, uptime, procesos, hash/verificar archivo, permisos, logs
    reporter.py        # reportes 10/10 en reportes/ (HTML + TXT + CSV + PDF + index)
    gospeed.py         # puente a Go: scan/DNS rápidos, con respaldo Python
  go/                  # darkly-go: scan concurrente + DNS DoH en Go (requiere Go 1.21+)
    go.mod main.go
  reportes/
    index.html         # índice de todos los reportes
    reporte_IP_*.html  # informe con mapa, puertos, ping, headers
    reporte_IP_*.txt   # 8 secciones + resumen ejecutivo
    reporte_IP_*.csv   # tabla campo,valor para Excel
    reporte_IP_*.pdf   # PDF simple sin dependencias
```

## Uso rápido

```bash
cd darkly-tools
pip install -r requirements.txt
python darkly.py
```

Menú principal: `1) Redes  2) Seguridad  3) Recolección info  4) Sistema  5) IP / Info por IP`.
Redes incluye `7) DNS rápido Go` y `8) Escaneo rápido Go` (piden autorización igual).

## Módulo Go v2.1.0 (todos los módulos, standalone)

`darkly-go menu` corre todo sin Python. Comandos JSON: `scan dns ping subnet traceroute hash hashid pass genpass audit breach headers urlscan ipinfo ptr rdap whois user dnsrecords subdomains ghuser sysinfo filehash verify report menu version`.

```bash
# Instala Go 1.21+ desde https://go.dev/dl/ (o: winget install GoLang.Go)
cd darkly-tools/go
go build -o darkly-go.exe .
./darkly-go.exe scan --host 127.0.0.1 --ports 22,80,443
./darkly-go.exe audit 'mi-clave'
./darkly-go.exe report --ip 8.8.8.8 --nombre casa
./darkly-go.exe menu
```

Sin Go instalado el menú Python usa su propio código automáticamente (más lento pero igual de preciso). Desde Python: `tools.gospeed.go_run("hashid", "...")`.

## Sección IP (auto-guarda)

Acepta IP o dominio (`8.8.8.8` o `google.com`), resuelve y pide nombre específico:
- `1) Mi IP`, `2) Geo por IP`, `3) PTR`, `4) RDAP`, `5) Informe 10/10`, `6) Ver reportes`
- Opciones 1-4 auto-guardan HTML+TXT+CSV+PDF rápido (geo+PTR+RDAP)
- Opción 5 informe completo: + ping + top puertos (22,80,443,8080,3389) con banner + headers + mapa

Abre `reportes/index.html` en el navegador para verlos.

## Precisión anti-fallos

- DNS: sistema + respaldo DoH Cloudflare
- IP: multi-fuente ip-api → ipapi.co → ipwho.is, con validación y normalización
- Subdominios: crt.sh con reintentos + respaldo HackerTarget
- RDAP por HTTPS (no falla aunque bloqueen puerto 43 de WHOIS)
- Headers con reintento HEAD→GET, errores claros
- Puertos con banner real, no solo abierto/cerrado
