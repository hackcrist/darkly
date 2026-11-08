"""Pruebas básicas para Darkly Tools (Python)."""

import importlib

import pytest


def test_darkly_version():
    """darkly.py debe exponer __version__."""
    import darkly

    assert hasattr(darkly, "__version__")
    assert darkly.__version__ == "2.0.0"


def test_tools_modules_importan():
    """Los módulos de tools deben poder importarse sin errores."""
    modulos = [
        "tools.networking",
        "tools.security",
        "tools.gathering",
        "tools.system_tools",
        "tools.reporter",
        "tools.username",
        "tools.gospeed",
    ]
    for nombre in modulos:
        importlib.import_module(nombre)


def test_security_hash_retorna_str():
    """security.hash_string debe retornar una cadena no vacía."""
    from tools.security import hash_string

    resultado = hash_string("prueba", algoritmo="sha256")
    assert isinstance(resultado, str)
    assert len(resultado) > 0
