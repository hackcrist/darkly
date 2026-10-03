# Darkly Tools

Colección de herramientas de Linux, redes y seguridad con interfaz de terminal en español. El proyecto se distribuye en dos implementaciones equivalentes: `darkly.py` (Python, versión 2.0.0) y `darkly-go` (Go, versión 2.1.0). Ambas comparten el mismo modelo de menús y generan reportes idénticos. Su valor diferencial es la precisión defensiva: cada consulta usa múltiples fuentes con respaldo automático y explica sus límites en vez de fallar en silencio.

---

## Arquitectura del Sistema

El sistema se organiza en dos frentes que se comunican mediante JSON por salida estándar. Python invoca cualquier subcomando Go con `tools.gospeed.go_run(...)` y, si el binario no existe, recurre a su propia implementación.

---

## Mapa de Documentación

### 1. Arquitectura
* **[General](01-Arquitectura/index.md):** capas, flujo de datos y ciclo de ejecución.
* **[Componentes](01-Arquitectura/componentes.md):** archivos fuente y funciones principales.

### 2. Uso
* **[General](02-Uso/index.md):** menús interactivos y comandos directos.
* **[Instalación](02-Uso/instalacion.md):** requisitos, dependencias y Termux.

### 3. Referencia
* **[General](03-Referencia/index.md):** variables de entorno y códigos de salida.
* **[API web](03-Referencia/api.md):** endpoints, parámetros y autenticación.
* **[Errores](03-Referencia/errores.md):** fallos conocidos y resolución.

---

## Inicio Rápido

```bash
git clone https://github.com/hackcrist/darkly.git
cd darkly
pip install -r requirements.txt
python darkly.py
```
