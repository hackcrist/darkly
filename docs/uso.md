# Uso

```bash
python darkly.py
```

## 1) Redes

- **DNS**: acepta host o dominio, con respaldo DoH si falla el sistema.
- **Ping**: 2 paquetes, salida decodificada a UTF-8.
- **Puertos**: pide confirmación de autorización, luego escanea y lee el banner de cada puerto abierto.
- **Traceroute, subred y banner**: diagnóstico de ruta, cálculo CIDR y lectura de banner puntual.
- **Opciones Go**: `7` y `8` usan el binario Go si está compilado.

## 2) Seguridad

- **Hash e identificar**: calcula o reconoce MD5, SHA-1, SHA-256 y SHA-512.
- **Fortaleza y generador**: puntúa tu clave y genera una auto-verificada contra filtraciones.
- **Cabeceras**: revisa las 6 de seguridad en cualquier URL.
- **URL**: puntúa riesgo de phishing de 0 a 100 con hallazgos.
- **Auditoría (7)**: fortaleza más filtración HIBP en una pasada, con veredicto final.

## 3) Recolección

IP pública y por IP, cabeceras HTTP, PTR preciso, WHOIS, RDAP, búsqueda de usuarios en 17 sitios, registros DNS, subdominios crt.sh y perfil GitHub. Las consultas de IP se auto-guardan (ver [Reportes](reportes.md)).

## 4) Sistema

Info del equipo, disco, CPU/RAM, uptime, procesos, hash y verificación de archivos, permisos y cola de logs. Todo local.

## 5) IP

Acepta IP o dominio y nombre específico para el archivo. La opción 5 genera el informe completo (geo, PTR, RDAP, ping, puertos, headers y mapa) en 4 formatos. La 6 lista lo guardado.
