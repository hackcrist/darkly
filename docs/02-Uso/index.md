# Uso

Esta sección cubre la operación diaria: menús interactivos, comandos directos e instalación.

---

## Módulos y Especificaciones

* **[Instalación](instalacion.md):** requisitos, dependencias, compilación de Go y Termux.

---

## Flujo de Trabajo

```
Inicio (python darkly.py / darkly-go menu)
  → Menú principal: Redes, Seguridad, Recolección, Sistema, IP
    → Submenú de categoría
      → Entrada validada → Consulta → Tabla en pantalla
        → Auto-guardado en reportes/ (solo IPs y usuarios)
```

El escaneo de puertos y las versiones de servicios exigen confirmación explícita de autorización antes de ejecutarse.
