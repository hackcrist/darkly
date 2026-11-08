# Darkly Tools - Registro de cambios

## [2.0.0] - 2026-11-08

### Agregado
- Menú interactivo en Python con colores neon y soporte para `darkly-go` (Go).
- API web Flask con autenticación por token (`DARKLY_TOKEN`) y límite de peticiones por IP.
- Reportes en HTML, TXT, CSV, PDF y JSON con SHA-256 de integridad.
- Instalador multiplataforma (`install.py`): Termux, Linux (apt/pacman), Windows, macOS.
- Excepciones personalizadas (`exceptions.py`): `DarklyError` y 5 subclases.
- Logging estructurado (`logging`) en stderr.
- Type hints en `darkly.py` y `webapp.py`.
- Pruebas unitarias (pytest para Python, go test para Go).
- CI con GitHub Actions en Ubuntu, Windows y macOS.
- Dockerfile y docker-compose.yml para desplegar la API.
- Linting automático con ruff, black y gofmt (pre-commit + CI).

### Cambiado
- `webapp.py` exige `DARKLY_TOKEN` obligatorio al iniciar.
- `darkly.py` asegura `sys.path` para importar `tools/` desde cualquier carpeta.
- `install.py` detecta automáticamente el gestor de paquetes del sistema.

### Corregido
- Tests de Python encontraban módulos `darkly` y `tools` sin configurar `sys.path`.
- Nombre correcto de función `hash_text` (no `hash_string`) en pruebas de seguridad.

---

## [1.0.0] - 2026-10-30

### Agregado
- Primera versión pública de Darkly Tools.
- Módulos de redes, seguridad, OSINT y sistema.
- Implementación en Python y en Go.

---

### Cómo contribuir

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para enviar mejoras, reportar errores o propar funcionalidades.
