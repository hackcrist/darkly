# Reportes

Cada consulta de IP genera 4 archivos en `reportes/` (carpeta auto-creada, excluida de git) más el índice `index.html`.

## Formatos

- **HTML**: tarjetas por sección, mapa embebido con coordenadas, badges de riesgo.
- **TXT**: 8 secciones (geo, PTR, RDAP, DNS, ping, puertos, headers, resumen ejecutivo).
- **CSV**: tabla campo/valor, lista para Excel.
- **PDF**: documento simple de una página, sin dependencias.

## Nombre específico

Al consultar puedes dar un nombre para el archivo (`--nombre casa` o en el menú), y aceptar IP o dominio (se resuelve y se guardan ambos).

## Búsquedas de usuario

La opción de usuarios guarda `reporte_user_<nombre>_<fecha>.txt` con el estado por sitio. Los sitios con login o JS se marcan como indicio y conviene verificarlos a mano.
