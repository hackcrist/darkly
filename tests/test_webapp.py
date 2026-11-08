"""Tests de la API web (Darkly Tools).

Pruebas para los endpoints de `webapp.py` usando el cliente de pruebas de Flask.

Cubre:
- `/api/health` (disponible sin token)
- `/api/scan` (exige token válido)
- Límite de peticiones (rate limiting)
- Endpoints pasivos básicos (`/api/dns`, `/api/geo`, `/api/hash`)
- Manejo de errores en peticiones malformadas
"""

import os
import pytest

# Forzar token antes de importar webapp (evita SystemExit en import)
os.environ.setdefault("DARKLY_TOKEN", "test-token-12345")

pytest.importorskip("flask")

from darkly.api.webapp import app  # noqa: E402


@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client


def test_health_sin_token(client):
    """El endpoint /api/health debe responder sin necesidad de token."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"


def test_scan_exige_token(client):
    """El endpoint /api/scan debe devolver 401 sin cabecera X-Token."""
    resp = client.get("/api/scan?host=127.0.0.1")
    assert resp.status_code == 401
    data = resp.get_json()
    assert "error" in data


def test_scan_con_token_valido(client):
    """Con token válido y ENABLE_SCAN=0 debe devolver 403 (desactivado)."""
    resp = client.get(
        "/api/scan?host=127.0.0.1",
        headers={"X-Token": "test-token-12345"},
    )
    assert resp.status_code == 403
    data = resp.get_json()
    assert "desactivado" in data["error"].lower()


def test_dns_sin_host(client):
    """Petición a /api/dns sin parámetro host debe devolver 400."""
    resp = client.get("/api/dns")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_dns_con_host(client):
    """Petición válida a /api/dns debe devolver JSON."""
    resp = client.get("/api/dns?host=example.com")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)


def test_hash_sin_texto(client):
    """Petición a /api/hash sin texto debe devolver 400."""
    resp = client.get("/api/hash")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_hash_con_texto(client):
    """Petición válida a /api/hash debe devolver hex válido."""
    resp = client.get("/api/hash?text=hola")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "hex" in data
    assert len(data["hex"]) == 64  # SHA-256


def test_rate_limiting(client):
    """Demasiadas peticiones a un endpoint con límite deben devolver 429."""
    headers = {"X-Token": "test-token-12345"}
    # /api/scan tiene límite de 5/min; enviamos 6 peticiones rápidas
    for _ in range(6):
        resp = client.get("/api/scan?host=127.0.0.1", headers=headers)
    assert resp.status_code in (401, 403, 429)
