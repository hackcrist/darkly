"""Puente Python -> Go para módulos rápidos (scan + DNS).

Si Go está instalado compila el binario una vez y lo usa.
Si no, lanza RuntimeError y el menú usa el Python como respaldo.
"""
import json
import os
import shutil
import subprocess

GO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "go")
BIN_NAME = "darkly-go.exe" if os.name == "nt" else "darkly-go"
BIN_PATH = os.path.join(GO_DIR, BIN_NAME)
SRC_PATH = os.path.join(GO_DIR, "main.go")


def go_available() -> bool:
    return shutil.which("go") is not None


def ensure_binary() -> str:
    """Devuelve la ruta del binario compilado o lanza RuntimeError."""
    if os.path.isfile(BIN_PATH) and os.path.getmtime(BIN_PATH) >= os.path.getmtime(SRC_PATH):
        return BIN_PATH
    if not go_available():
        raise RuntimeError("Go no está instalado. Instálalo (https://go.dev/dl/) y reintenta. Respaldo: usa la opción Python.")
    r = subprocess.run(["go", "build", "-o", BIN_PATH, "."], cwd=GO_DIR,
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not os.path.isfile(BIN_PATH):
        raise RuntimeError(f"No se pudo compilar darkly-go: {(r.stderr or r.stdout)[:300]}")
    return BIN_PATH


def go_port_scan(host: str, ports: str, timeout_ms: int = 1000, workers: int = 100) -> dict:
    return go_run("scan", "--host", host, "--ports", ports,
                 "--timeout", str(timeout_ms), "--workers", str(workers))


def go_dns_lookup(host: str) -> dict:
    return go_run("dns", "--host", host)


def go_run(*args: str, timeout: int = 120) -> dict:
    """Llama cualquier subcomando darkly-go y devuelve el JSON.
    Ej: go_run("hash", "--algo", "sha256", "hola")"""
    binp = ensure_binary()
    r = subprocess.run([binp, *args], capture_output=True, text=True, timeout=timeout)
    if not r.stdout.strip():
        raise RuntimeError(f"darkly-go no devolvió nada: {r.stderr[:200]}")
    return json.loads(r.stdout)
