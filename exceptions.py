"""Excepciones personalizadas para Darkly Tools.

Jerarquía:
    DarklyError (base)
      ├─ ConfigError
      ├─ NetworkError
      ├─ ToolError
      ├─ SecurityError
      └─ ReportError
"""

__all__ = [
    "DarklyError",
    "ConfigError",
    "NetworkError",
    "ToolError",
    "SecurityError",
    "ReportError",
]


class DarklyError(Exception):
    """Excepción base de Darkly Tools."""

    def __init__(self, mensaje: str, codigo: int = 1):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo

    def __str__(self) -> str:
        return f"[DarklyError] {self.mensaje}"


class ConfigError(DarklyError):
    """Errores de configuración (variables de entorno, tokens, rutas)."""


class NetworkError(DarklyError):
    """Errores de red (DNS, ping, HTTP, tiempo de espera)."""


class ToolError(DarklyError):
    """Errores de herramientas externas (Go, nmap, etc.)."""


class SecurityError(DarklyError):
    """Errores de seguridad (hashes, contraseñas, auditoría)."""


class ReportError(DarklyError):
    """Errores al generar reportes (HTML, PDF, CSV, JSON)."""
