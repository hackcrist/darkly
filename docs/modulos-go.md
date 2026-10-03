# Módulos Go

`darkly-go` replica todo en Go con salida JSON. Sin dependencias externas salvo `golang.org/x/text` (decodificación OEM).

```bash
cd go
go build -o darkly-go.exe .   # en Linux: go build -o darkly-go .
./darkly-go.exe menu
```

## Comandos

| Comando | Ejemplo |
|---|---|
| `scan` | `--host 127.0.0.1 --ports 22,80,443` |
| `dns` | `--host google.com` |
| `ping` | `8.8.8.8` |
| `subnet` | `192.168.1.0/24` |
| `traceroute` | `google.com` |
| `hash` | `--algo sha256 hola` |
| `hashid` | `d41d8cd98f00b204e9800998ecf8427e` |
| `pass` / `genpass` / `audit` / `breach` | `audit 'mi-clave'` |
| `headers` / `urlscan` | `urlscan https://...` |
| `ipinfo` / `ptr` / `rdap` / `whois` | `ipinfo 8.8.8.8` |
| `user` | `torvalds` |
| `dnsrecords` / `subdomains` / `ghuser` | `subdomains google.com` |
| `sysinfo` / `filehash` / `verify` | `filehash --algo sha256 archivo` |
| `report` | `--ip 8.8.8.8 --nombre casa` |
| `menu` / `version` | interactivo / versión |

## Puente con Python

Desde Python, cualquier subcomando:

```python
from tools.gospeed import go_run
go_run("hashid", "d41d8cd98f00b204e9800998ecf8427e")
```

Si Go no está instalado, el menú Python usa su propio código automáticamente.
