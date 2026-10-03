# Referencia

Tablas de consulta rápida: variables de entorno, API web y catálogo de errores.

---

## Módulos y Especificaciones

* **[API web](api.md):** endpoints, parámetros, autenticación y despliegue.
* **[Errores](errores.md):** fallos conocidos, causa y resolución.

---

## Flujo de Trabajo

```
Variable de entorno → comportamiento
Endpoint + parámetros → JSON
Error observado → tabla de errores → acción correctiva
```

## Variables de entorno (webapp.py)

| Variable | Defecto | Efecto |
| :--- | :--- | :--- |
| `DARKLY_TOKEN` | vacío | Token exigido en cabecera `X-Token` para `/api/scan` |
| `ENABLE_SCAN` | `0` | En `1` activa el escaneo (requiere token válido) |
| `RATE_LIMIT_ENABLED` | `1` | En `0` desactiva los límites (solo desarrollo local) |
| `TRUST_PROXY` | `0` | En `1` confía en `X-Forwarded-For` (solo detrás de proxy propio) |
| `PORT` | `5000` | Puerto de escucha |

## Códigos de salida (CLI)

| Código | Significado |
| :--- | :--- |
| `0` | Ejecución correcta |
| `1` | Error de red, resolución o validación (mensaje en `stderr` o JSON con `error`) |
| `2` | Uso incorrecto (faltan argumentos o comando desconocido) |
