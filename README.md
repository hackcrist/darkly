# Darkly Tools

<p align="center">
  <img src="assets/logo.svg" alt="Darkly Tools" width="600">
</p>

<p align="center">
  <img src="assets/badge-python.svg" alt="Python 3.10+">
  <img src="assets/badge-go.svg" alt="Go 1.21+">
  <img src="assets/badge-license.svg" alt="License MIT">
  <img src="assets/badge-version.svg" alt="Version 2.0">
  <img src="assets/badge-platform.svg" alt="Windows y Linux">
</p>

Colección de herramientas de redes, seguridad y OSINT pasivo para la terminal, en español y con menús a color. Incluye una implementación en Python (`darkly.py`), su gemela en Go (`darkly-go`) con los mismos módulos, y una API web opcional.

> **Solo fines educativos.** Úsalo con responsabilidad y autorización. El escaneo de puertos exige confirmación explícita.

## Características

- **Redes:** DNS con respaldo DoH, ping, traceroute, calculadora de subred, banner grab y escaneo de puertos concurrente con tabla estilo nmap.
- **Seguridad:** hashes e identificación, fortaleza y generador de contraseñas, cabeceras HTTP, detector de phishing y auditoría HIBP con k-anonymity.
- **OSINT pasivo:** GeoIP de tres fuentes con ASN y verificación de acuerdos, PTR, RDAP, WHOIS, registros DNS, subdominios (crt.sh), perfil de GitHub y búsqueda en 17 sitios.
- **Sistema:** info y disco, CPU/RAM, uptime, procesos, hash y verificación de archivos, permisos y logs.
- **Reportes:** informe detallado por IP en HTML, TXT, CSV, PDF y JSON de evidencia con SHA-256.
- **Python + Go:** el menú en Python llama a los subcomandos Go por JSON y, si Go no está instalado, usa su propio código.

## Requisitos

- Python 3.10 o superior (obligatorio).
- Go 1.21 o superior (opcional, activa los módulos rápidos).
- Conexión a internet para las fuentes OSINT.

Verificado en Python 3.12 y Go 1.27 sobre Windows. Los módulos locales (hash, subredes, permisos, reportes) funcionan sin internet.

## Instalación

```bash
git clone https://github.com/hackcrist/darkly.git
cd darkly
pip install -r requirements.txt

# Go opcional (habilita los módulos rápidos)
cd go && go build -o darkly-go.exe .   # en Linux: go build -o darkly-go .
```

O con el instalador, que detecta el sistema, instala dependencias y compila Go:

```bash
python install.py            # Termux, Linux y Windows
python install.py --dry-run  # solo muestra lo que haría, sin cambios
```

En Android usa Termux (desde F-Droid o GitHub, nunca Play Store): `pkg install git python -y`, clona el repositorio y ejecuta `python install.py`. Sin root funciona todo excepto algunos modos de traceroute.

## Uso

```bash
python darkly.py            # menú interactivo en Python
python darkly.py --version  # ver versión
go/darkly-go.exe menu       # menú 100% en Go
```

Módulos del menú principal:

- **Redes:** DNS con DoH, ping, escaneo de puertos, traceroute, subredes, banner grab y versiones rápidas en Go.
- **Seguridad:** hash e identificación, fortaleza y generador, cabeceras, análisis de URL y auditoría HIBP.
- **Recolección:** mi IP, consulta de IP, cabeceras HTTP, PTR, WHOIS, RDAP, usuarios, registros DNS, subdominios y GitHub.
- **Sistema:** info y disco, uptime, procesos, hash y verificación de archivos, permisos y logs.
- **IP:** mi IP, info por IP, PTR, RDAP e informe completo con auto-guardado.

### Comandos Go

`darkly-go` expone cada módulo como subcomando con salida JSON. En Linux sustituye `./darkly-go.exe` por `./darkly-go`.

| Comando | Uso |
|---|---|
| `scan` | `--host 127.0.0.1 --ports 22,80,443 [--timeout 1000] [--workers 100]` |
| `dns` | `--host google.com` |
| `ping` | `google.com` |
| `subnet` | `192.168.1.0/24` |
| `traceroute` | `[--hops 20] google.com` |
| `hash` | `[--algo sha256] "texto"` |
| `hashid` | `5d41402abc4b2a76b9719d911017c592` |
| `pass` | `"contraseña"` |
| `genpass` | `[--n 16]` |
| `audit` | `"contraseña"` |
| `breach` | `"contraseña"` |
| `headers` | `https://ejemplo.com` |
| `urlscan` | `https://ejemplo.com` |
| `ipinfo` | `8.8.8.8` o `mia` (mi IP pública) |
| `ptr` | `8.8.8.8` |
| `rdap` | `google.com` o `8.8.8.8` |
| `whois` | `google.com` |
| `user` | `torvalds` |
| `dnsrecords` | `google.com` |
| `subdomains` | `google.com` |
| `ghuser` | `torvalds` |
| `sysinfo` | Sin argumentos |
| `filehash` | `[--algo sha256] archivo` |
| `verify` | `[--algo sha256] archivo hash` |
| `report` | `--ip 8.8.8.8 [--objetivo casa.com] [--nombre casa] [--outdir reportes]` |
| `menu` | Menú interactivo en Go |
| `version` | Versión |

```bash
./darkly-go.exe scan --host 127.0.0.1 --ports 22,80,443   # escaneo concurrente
./darkly-go.exe ipinfo 8.8.8.8                            # geo triple fuente con ASN
./darkly-go.exe report --ip 8.8.8.8 --nombre casa         # informe completo
```

## Capturas

<p align="center">
  <img src="assets/windows-terminal.png" alt="Darkly en Windows Terminal" width="700">
</p>

| Web | Termux |
|---|---|
| <img src="assets/web.png" alt="Darkly Web" width="300"> | <img src="assets/termux.jpeg" alt="Termux" width="130"> |

## Reportes

Cada consulta de IP genera cinco archivos en `reportes/` (carpeta auto-creada, no se sube a git) más un índice `index.html`:

- **TXT** de 10 secciones: geo, PTR, RDAP, DNS, ping, puertos con servicio, cabeceras, verificación multi-fuente, evidencia y resumen.
- **HTML** con mapa embebido cuando hay coordenadas.
- **CSV** en formato campo/valor y **PDF** simple sin dependencias.
- **JSON** de evidencia con los datos en bruto y su SHA-256.

El SHA-256 de la evidencia se imprime en el resto de formatos, así se puede comprobar que el informe no se alteró (`certutil -hashfile reporte_IP_casa_20261018_153000.json SHA256` en Windows o `sha256sum` en Linux). Los nombres llevan marca de tiempo y los puertos se listan con servicio al estilo nmap (PORT / STATE / SERVICE / DETALLE).

## API web

`webapp.py` expone las consultas pasivas por HTTP con límite por IP y minuto. Por defecto escucha en `http://127.0.0.1:5000`.

```bash
pip install -r requirements-web.txt
python webapp.py
```

`web/` incluye una demo mínima. El escaneo está desactivado por defecto. Endpoints, autenticación y variables de entorno: **[docs/03-Referencia/api.md](docs/03-Referencia/api.md)**.

## Estructura

```
darkly.py            # menú neón en español
install.py           # instalador multiplataforma (Termux/Linux/Windows)
webapp.py + web/     # API + web pública (Flask, segura por defecto)
tools/               # networking, security, gathering, username, system_tools, reporter, gospeed
go/                  # darkly-go v2.1 con los mismos módulos en Go
docs/                # manuales en español (arquitectura, uso, referencia)
reportes/            # se auto-crea al usarlo (no se sube a git)
assets/              # logo y capturas del README
```

## Compatibilidad

| Función | Windows | Linux | Termux/Android |
|---|---|---|---|
| Menú Python y módulos | Sí | Sí | Sí |
| `darkly-go` | Sí | Sí | Sí |
| Ping y traceroute | Sí | Sí | Reducido sin root |
| Reportes (HTML/TXT/CSV/PDF/JSON) | Sí | Sí | Sí |
| API web (Flask) | Sí | Sí | Sí |

macOS no está cubierto por el instalador, aunque los módulos de Python y Go funcionan si las herramientas del sistema están presentes.

## Seguridad y uso responsable

- **Solo objetivos propios o autorizados.** El escaneo de puertos exige confirmación explícita y está desactivado en la API pública.
- **Modo pasivo.** Sin exploits, sin logins, sin fuerza bruta; los hashes y las contraseñas se procesan en local.
- **Contraseñas.** La verificación HIBP solo envía 5 caracteres del SHA-1 (k-anonymity); en la API va por `POST`, nunca en la URL.
- **Sin secretos en el código.** No hay claves ni tokens embebidos; todo va por variables de entorno.

## Documentación

- [Manual completo](docs/index.md)
- [Arquitectura](docs/01-Arquitectura/index.md)
- [Uso e instalación](docs/02-Uso/index.md)
- [Referencia: API, variables y errores](docs/03-Referencia/index.md)

## Licencia

MIT. Consulta el archivo [LICENSE](LICENSE).

## Autor

**Crist Code** — https://github.com/hackcrist/darkly

Si te sirve, deja una estrella en GitHub.
