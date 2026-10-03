# Componentes

Ubicación y responsabilidad de cada pieza del repositorio. Firmas verificadas del código fuente.

---

## Especificación Técnica

### Núcleo interactivo

| Archivo | Responsabilidad |
| :--- | :--- |
| `darkly.py` | Menú principal, submenús por categoría, confirmación de autorización |
| `go/main.go` | Despachador de 22 subcomandos y salida JSON (`emitJSON`) |
| `go/menu.go` | Menú interactivo equivalente en Go |
| `webapp.py` | API Flask y página web con límites por IP |

### Módulos Python (`tools/`)

| Archivo | Funciones principales |
| :--- | :--- |
| `networking.py` | `dns_lookup(host, timeout=8)`, `port_scan(host, ports, timeout=1.0, workers=50)`, `banner_grab(host, port, timeout=3.0)`, `ping_host(host, count=2, timeout=2)`, `traceroute(host, max_hops=20, timeout=2)`, `subnet_info(cidr)`, `parse_ports(port_str)` |
| `security.py` | `hash_text(text, algo='sha256')`, `identify_hash(h)`, `password_strength(password)`, `generate_password(length=16)`, `check_security_headers(url, timeout=10)`, `scan_url(url)`, `check_password_breach(password, timeout=10)`, `audit_password(password, timeout=10)` |
| `gathering.py` | `public_ip_info(timeout=10)`, `ip_lookup(ip, timeout=10)`, `http_headers(url, timeout=10)`, `reverse_dns(ip, timeout=8)`, `whois_lookup(query, timeout=10)`, `rdap_lookup(query, timeout=12)`, `dns_records(domain, timeout=8)`, `subdomains_crtsh(domain, timeout=15, limit=50)`, `github_profile(user, timeout=10)` |
| `system_tools.py` | `sys_info()`, `disk_usage(path='.')`, `try_psutil_stats()`, `file_hash(path, algo='sha256')`, `file_hash_verify(path, esperado, algo='sha256')`, `get_uptime()`, `list_processes(limit=15)`, `check_permissions(path)`, `tail_log(path, lines=20)` |
| `username.py` | `search(username, timeout=10, workers=6)`, `validate_username(u)`, `save_report(username, results)` |
| `reporter.py` | `build_ip_report(ip, geo, ptr, rdap, nombre=None, objetivo='', extra=None)` retorna `(html, txt, csv, pdf)` |
| `gospeed.py` | `go_run(*args, timeout=120)`, `go_port_scan(host, ports, ...)`, `go_dns_lookup(host)`, `ensure_binary()` |

### Módulos Go (`go/`)

| Archivo | Comandos |
| :--- | :--- |
| `main.go` | `scan`, `dns`, `version` |
| `netx.go` | `ping`, `subnet`, `traceroute` y núcleos `dnsCore`, `pingCore`, `scanCore` |
| `sec.go` | `hash`, `hashid`, `pass`, `genpass`, `audit`, `breach`, `headers`, `urlscan` |
| `osint.go` | `ipinfo`, `ptr`, `rdap`, `whois`, `user`, `dnsrecords`, `subdomains`, `ghuser` |
| `sys.go` | `sysinfo`, `filehash`, `verify` |
| `report.go` | `report` (HTML, TXT, CSV y PDF mínimo) |

---

## Consideraciones Críticas y Casos de Borde

1. **Concurrencia:** el escaneo usa 50 hilos en Python y 100 goroutines en Go; un objetivo lento no bloquea al resto por los timeouts por puerto.
2. **Límites de recursos:** `file_hash` rechaza archivos mayores de 500 MB; `parse_ports` limita rangos a 1024 puertos.
3. **Manejo de fallas:** cada fuente externa tiene respaldo encadenado y toda falla de red se devuelve como `{"error": ...}` en vez de excepciones no controladas.

---

## Ejemplo de Uso

```python
from tools.gathering import ip_lookup
from tools import reporter

geo = ip_lookup("8.8.8.8")
html, txt, csv, pdf = reporter.build_ip_report("8.8.8.8", geo, "dns.google", {"nombre": "GOGL"})
```

```bash
./darkly-go.exe report --ip 8.8.8.8 --nombre casa
```
