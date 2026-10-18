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

---

## Mapa de Menús

Menú principal y submenús de `darkly.py` (equivalentes en `darkly-go menu`):

- **1 Redes:** `1` DNS con respaldo DoH · `2` ping · `3` escaneo de puertos (pide autorización) · `4` traceroute · `5` calculadora de subred · `6` banner grab · `7` DNS rápido en Go · `8` escaneo rápido en Go.
- **2 Seguridad:** `1` generar hash · `2` identificar hash · `3` fortaleza de contraseña · `4` generar contraseña (auto-verificada) · `5` cabeceras de seguridad · `6` analizar URL · `7` auditoría completa (fortaleza + filtración).
- **3 Recolección:** `1` mi IP pública · `2` consultar IP · `3` cabeceras HTTP · `4` DNS inverso · `5` WHOIS · `6` RDAP · `7` usuarios (17 sitios) · `8` registros DNS · `9` subdominios · `10` perfil GitHub.
- **4 Sistema:** `1` info + disco + CPU/RAM · `2` uptime · `3` procesos · `4` hash de archivo · `5` verificar hash · `6` permisos · `7` ver final de un log.
- **5 IP:** `1` mi IP · `2` info por IP · `3` PTR · `4` RDAP · `5` informe completo + guardar · `6` ver reportes guardados.
