# Contribuir a Darkly Tools

Gracias por interesarte en mejorar **Darkly**. Este documento explica cómo reportar errores, proponer cambios y enviar pull requests.

## 1. Código de conducta

- Sé respetuoso con otros colaboradores.
- Este proyecto tiene fines **educativos**; no uses las herramientas para atacar sistemas sin autorización escrita.
- No subas secretos, tokens ni contraseñas reales al repositorio.

## 2. Antes de empezar

1. Haz un **fork** del repositorio.
2. Clona tu fork:
   ```bash
   git clone https://github.com/TU_USUARIO/darkly.git
   cd darkly
   ```
3. Crea una rama para tu cambio:
   ```bash
   git checkout -b mejora/descripcion-corta
   ```

## 3. Entorno de desarrollo

Instala dependencias de desarrollo:

```bash
pip install -r requirements-dev.txt
pre-commit install
```

## 4. Estándares de código

- **Python**: sigue PEP 8. El proyecto usa `ruff` y `black`.
- **Go**: sigue `gofmt`.
- Usa type hints en funciones públicas.
- Los mensajes de error en español deben ser claros y no exponer datos sensibles.

Antes de commitear, ejecuta:

```bash
ruff check .
black .
gofmt -l go/
pytest tests/ -v
```

## 5. Envío de cambios

1. Haz commit con mensaje descriptivo:
   ```
   feat: agregar endpoint /api/ping
   fix: corregir puerto por defecto en webapp.py
   docs: actualizar instrucciones de Docker
   ```
2. Sube tu rama:
   ```bash
   git push origin mejora/descripcion-corta
   ```
3. Abre un **Pull Request** en GitHub hacia la rama `main`.

## 6. Reportar errores

Abre un issue en GitHub con:
- Versión de Darkly (`python darkly.py --version`).
- Sistema operativo y versión de Python/Go.
- Pasos para reproducir el error.
- Mensaje de error completo (captura o texto).

## 7. Seguridad

No reports vulnerabilidades por issues públicos. Escríbeles al mantenedor por canales privados si descubres algo crítico.

## Licencia

Al contribuir, aceptas que tu código se distribuya bajo la licencia MIT del proyecto.
