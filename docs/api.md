# API web

```bash
pip install -r requirements-web.txt
python webapp.py   # http://127.0.0.1:5000
```

## Endpoints

Todos GET con límite por IP y minuto, salvo indicación:

| Endpoint | Parámetro | Notas |
|---|---|---|
| `/api/health` | — | Estado del servidor |
| `/api/dns` | `?host=` | DNS sistema + DoH |
| `/api/geo` | `?ip=` | GeoIP triple fuente |
| `/api/ptr` | `?ip=` | Reverso preciso |
| `/api/rdap` | `?q=` | Registro por HTTPS |
| `/api/headers` | `?url=` | Cabeceras HEAD y GET |
| `/api/urlscan` | `?url=` | Riesgo 0-100 |
| `/api/hash` | `?text=&algo=` | Hash local |
| `/api/subdomains` | `?domain=` | crt.sh con respaldo |
| `/api/ghuser` | `?u=` | Perfil GitHub |
| `/api/user` | `?u=` | 17 sitios (lento, límite 5/min) |
| `POST /api/breach` | JSON `{"password":"..."}` | k-anonymity, nunca en URL |
| `/api/scan` | `?host=&ports=` | Desactivado por defecto |

Ejemplo:

```bash
curl "http://127.0.0.1:5000/api/geo?ip=8.8.8.8"
curl -X POST -H "Content-Type: application/json" \
  -d '{"password":"password123"}' http://127.0.0.1:5000/api/breach
```

## Variables

| Variable | Defecto | Efecto |
|---|---|---|
| `DARKLY_TOKEN` | vacío | Token exigido en `X-Token` para `/api/scan` |
| `ENABLE_SCAN` | `0` | En `1` activa el escaneo (requiere token) |
| `RATE_LIMIT_ENABLED` | `1` | En `0` quita límites (solo local) |
| `TRUST_PROXY` | `0` | En `1` confía en `X-Forwarded-For` (solo tras proxy propio) |
| `PORT` | `5000` | Puerto de escucha |

## Despliegue

Render o Railway: instalar con `requirements-web.txt`, arrancar con `gunicorn webapp:app` y definir `DARKLY_TOKEN` con `ENABLE_SCAN=0`.
