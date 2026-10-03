# Catálogo de Diagnósticos y Errores

Recopilación de condiciones de error emitidas por el sistema, con causa y resolución. Cubre Python y Go.

---

## Matriz de Errores

| Código | Nivel | Subsistema | Causa Raíz | Solución Técnica |
| :--- | :--- | :--- | :--- | :--- |
| `SSL/CERTIFICATE_VERIFY_FAILED` | Error | HTTPS (Python) | CA ausente o red con filtro TLS que intercepta | Instalar `certifi`; el programa prefiere endpoints que verifican limpio |
| `puerto 43 bloqueado` | Aviso | WHOIS | Red filtrada | Usar RDAP, que va por HTTPS |
| `502 crt.sh` | Transitorio | Subdominios | Servidor de crt.sh inestable | Automático: 3 reintentos y respaldo HackerTarget |
| `bloqueado (403/429)` | Aviso | Usuarios | Anti-bots del sitio | npm usa API oficial; el resto se verifica a mano |
| `Sin registro PTR` | Informativo | PTR | El dueño no creó reverso | Normal en móviles y nubes; no es falla |
| `Go no instalado` | Aviso | Puente | Binario ausente | El menú usa código Python; compilar con `go build` |
| `401 /api/scan` | Error | API | Falta token o `DARKLY_TOKEN` vacío | Definir token y enviar cabecera `X-Token` |
| `403 /api/scan` | Informativo | API | Escaneo apagado | Activar con `ENABLE_SCAN=1` |
| `429 límite excedido` | Aviso | API | Demasiadas peticiones por minuto | Esperar un minuto |
| `Rango muy grande` | Error | Puertos | Más de 1024 puertos (Python) o 2048 (Go) | Dividir el rango |
| `Archivo muy grande` | Error | Hash | Supera 500 MB | Verificar por partes o excluirlo |
