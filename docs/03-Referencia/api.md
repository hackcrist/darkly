# API web

La API expone las consultas pasivas por HTTP con límite por IP y minuto. Arranque: `pip install -r requirements-web.txt` y `python webapp.py` (escucha en el puerto `5000`).

---

## Especificación Técnica

### Endpoints GET

| Endpoint | Parámetro | Respuesta |
| :--- | :--- | :--- |
| `/api/health` | — | Estado del servidor |
| `/api/dns` | `?host=` | Resolución sistema más DoH |
| `/api/geo` | `?ip=` | GeoIP de triple fuente |
| `/api/ptr` | `?ip=` | Reverso preciso |
| `/api/rdap` | `?q=` | Registro por HTTPS |
| `/api/headers` | `?url=` | Cabeceras por HEAD y GET |
| `/api/urlscan` | `?url=` | Riesgo de 0 a 100 con hallazgos |
| `/api/hash` | `?text=` y `?algo=` | Hash calculado localmente |
| `/api/subdomains` | `?domain=` | crt.sh con respaldo |
| `/api/ghuser` | `?u=` | Perfil público de GitHub |
| `/api/user` | `?u=` | 17 sitios (lento, límite 5 por minuto) |
| `/api/scan` | `?host=` y `?ports=` | Desactivado por defecto (código 403) |

### Endpoint POST

`POST /api/breach` con cuerpo `{"password": "..."}`. La clave nunca viaja en la URL ni queda en registros del servidor.

```bash
curl "http://127.0.0.1:5000/api/geo?ip=8.8.8.8"
curl -X POST -H "Content-Type: application/json" \
  -d '{"password":"password123"}' http://127.0.0.1:5000/api/breach
```

### Autenticación del escaneo

`GET /api/scan` exige las dos condiciones: `ENABLE_SCAN=1` en el servidor y cabecera `X-Token` igual a `DARKLY_TOKEN`. Sin token responde 401; con escaneo apagado responde 403.

### Despliegue

Render o Railway con `gunicorn webapp:app`, variables `DARKLY_TOKEN` definida y `ENABLE_SCAN=0`.

---

## Consideraciones Críticas y Casos de Borde

1. **Límites por IP:** de 5 a 60 peticiones por minuto según el costo del endpoint; al exceder responde 429 con mensaje de espera.
2. **Confianza en proxy:** activar `TRUST_PROXY=1` solo detrás de un proxy propio; en internet directo permite falsificar la IP del límite.
3. **Limpieza de memoria:** el registro de peticiones se purga cada 120 segundos para evitar crecimiento indefinido.
