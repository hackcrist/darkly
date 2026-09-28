# Darkly Tools

<p align="center">
  <img src="assets/logo.svg" alt="Darkly Tools" width="600">
</p>

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Go](https://img.shields.io/badge/Go-1.21%2B-00ADD8?style=flat-square&logo=go&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Version](https://img.shields.io/badge/Version-2.0-ff00ff?style=flat-square)
![Platform](https://img.shields.io/badge/Windows%20%7C%20Linux-OK-00ffea?style=flat-square)

Colección educativa de herramientas de **Linux, redes y seguridad**, en español, con banner neón y menús con color. **Python + Go juntos**: lo mismo en ambos lenguajes, JSON entre ellos.

> 📚 **Solo fines educativos.** Úsalo con responsabilidad y autorización. El escaneo de puertos pide confirmación explícita.

## ✨ Funciones

| Módulo | Qué hace |
|---|---|
| 🌐 Redes | DNS con respaldo DoH, ping, escaneo de puertos + banner real, traceroute, subredes, versión rápida en Go |
| 🛡️ Seguridad | Hash/identificar, fortaleza y generador (auto-verificado), auditoría HIBP k-anonymity, cabeceras, detector de phishing |
| 🔎 OSINT pasivo | GeoIP triple fuente, PTR preciso, RDAP, WHOIS, registros DNS, subdominios crt.sh, GitHub, usuarios en 17 sitios |
| 🖥️ Sistema | Sysinfo, disco, CPU/RAM, uptime, procesos, hash y verificación de archivos, permisos, logs |
| 📁 IP / Info | Acepta IP o dominio, informe 10/10 con mapa, **auto-guarda HTML + TXT + CSV + PDF** |

## 🚀 Uso rápido

```bash
pip install -r requirements.txt
python darkly.py            # menú interactivo
python darkly.py --version  # ver versión

cd go
go build -o darkly-go.exe . # versión Go standalone
./darkly-go.exe menu
```

Menú: `1) Redes  2) Seguridad  3) Recolección  4) Sistema  5) IP`.

<p align="center">
  <img src="assets/demo.svg" alt="Menú Darkly Tools" width="520">
</p>

## 📁 Estructura

```
darkly.py            # menú neón en español
tools/               # networking, security, gathering, username, system_tools, reporter, gospeed
go/                  # darkly-go v2.1: los mismos módulos en Go (scan, dns, audit, report, menu...)
reportes/            # se auto-crea al usarlo (no se sube a git)
```

## 🎯 Precisión anti-fallos

- DoH por `one.one.one.one` (resiste redes con filtro TLS), geo triple con normalización
- RDAP por HTTPS en vez de WHOIS, crt.sh con reintentos + respaldo HackerTarget
- Ping/tracert decodificados OEM→UTF-8, puertos con banner real, URLs con heurística honesta

## 👤 Autor

**Crist Code** — https://github.com/hackcrist/darkly
