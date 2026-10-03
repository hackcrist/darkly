# Arquitectura

Esta sección describe las capas del sistema, el flujo de datos entre Python y Go y el ciclo de vida de una consulta.

---

## Módulos y Especificaciones

* **[Componentes](componentes.md):** archivos fuente, responsabilidades y funciones principales.

---

## Flujo de Trabajo

```
[Menú Python] ──JSON──> [darkly-go] ──> stdout ──> [Tabla / Reporte]
      │                                              ^
      └────── código propio (respaldo) ──────────────┘
```

1. El menú solicita un objetivo (IP o dominio) y lo valida con expresiones regulares.
2. La herramienta consulta fuentes públicas o el sistema local con tiempos de espera acotados.
3. El resultado se normaliza a diccionarios con claves estables (`ip`, `country`, `city`, `lat`, `lon`, `org`).
4. La salida se imprime en tabla y, para IPs, se persiste en `reportes/` en cuatro formatos más índice.
