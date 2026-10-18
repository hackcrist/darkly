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
4. La salida se imprime en tabla y, para IPs, se persiste en `reportes/` en cinco formatos más índice (HTML, TXT, CSV, PDF y JSON de evidencia con SHA-256).

---

## Consideraciones Críticas y Casos de Borde

1. **DNS:** primero el sistema y, si falla, DoH por `one.one.one.one`, que resiste redes con filtro TLS.
2. **GeoIP:** tres fuentes (ip-api, ipapi.co, ipwho.is) normalizadas, con ASN y verificación de acuerdos de país y ASN entre fuentes.
3. **Privacidad:** la auditoría HIBP usa k-anonymity (solo los 5 primeros caracteres del SHA-1); los hashes y las contraseñas se calculan en local.
4. **WHOIS y RDAP:** RDAP va por HTTPS porque el WHOIS clásico (puerto 43) suele estar bloqueado; los subdominios usan crt.sh con reintentos y respaldo HackerTarget.
5. **Salida:** las operaciones de red muestran su tiempo real y los puertos se listan con servicio al estilo nmap.
6. **SSL:** todas las funciones HTTPS usan los certificados de `certifi`.
