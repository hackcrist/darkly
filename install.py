#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Instalador Darkly Tools: Termux, Linux y Windows.

Uso:
  python install.py            # instala todo
  python install.py --dry-run  # solo muestra lo que haría
"""
import os
import platform
import shutil
import subprocess
import sys

C = {"c": "\033[38;2;0;255;234m", "g": "\033[38;2;57;255;20m",
     "y": "\033[38;2;255;255;0m", "r": "\033[38;2;255;49;49m",
     "b": "\033[1m", "e": "\033[0m"}
DRY = "--dry-run" in sys.argv


def say(msg, color="c"):
    print(f"{C[color]}{C['b']}{msg}{C['e']}")


def run(cmd, fatal=True, cwd=None):
    where = f" (en {cwd})" if cwd and cwd != os.getcwd() else ""
    say("$ " + " ".join(cmd) + where, "y" if DRY else "c")
    if DRY:
        return True
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        msg = f"Falló: {' '.join(cmd)}"
        if fatal:
            say(msg, "r")
            sys.exit(1)
        say(msg + " (opcional, continúo)", "y")
        return False
    return True


def is_termux():
    return os.path.isdir("/data/data/com.termux") or "com.termux" in (os.environ.get("PREFIX", ""))


def main():
    say("DARKLY TOOLS - Instalador", "c")
    here = os.path.dirname(os.path.abspath(__file__))
    system = platform.system().lower()

    if system != "windows" and not DRY:
        for f in ("darkly.py", "install.py"):
            p = os.path.join(here, f)
            try:
                os.chmod(p, 0o755)
                say(f"  permiso +x: {f}", "g")
            except Exception as e:
                say(f"  chmod {f} falló: {e}", "y")

    if is_termux():
        say("[1/4] pkg update...", "y")
        run(["pkg", "update", "-y"])
        say("[2/4] Paquetes del sistema...", "y")
        run(["pkg", "install", "-y", "python", "go", "git",
             "iputils", "traceroute", "procps", "clang"])
        req = "requirements-termux.txt"
    elif system == "linux":
        say("[1/4] apt update...", "y")
        run(["sudo", "apt", "update"])
        say("[2/4] Paquetes del sistema...", "y")
        run(["sudo", "apt", "install", "-y", "python3", "python3-pip",
             "golang", "git", "iputils-ping", "traceroute", "procps",
             "build-essential"])
        req = "requirements.txt"
    elif system == "windows":
        say("[1/4] Verificando Python y Go...", "y")
        for tool in ("python", "go"):
            if shutil.which(tool):
                say(f"  {tool} OK", "g")
            else:
                say(f"  {tool} no encontrado. Instálalo: Python desde python.org, "
                    "Go con: winget install GoLang.Go", "r")
        say("[2/4] (Windows no necesita paquetes del sistema)", "y")
        req = "requirements.txt"
    else:
        say(f"Sistema no reconocido: {system}", "r")
        sys.exit(1)

    say("[3/4] Dependencias Python...", "y")
    if not run([sys.executable, "-m", "pip", "install", "-r",
                os.path.join(here, req)], fatal=False):
        say("Reintentando solo con certifi...", "y")
        run([sys.executable, "-m", "pip", "install", "certifi"], fatal=False)

    say("[4/4] Compilando darkly-go...", "y")
    go_dir = os.path.join(here, "go")
    binary = os.path.join(go_dir, "darkly-go.exe" if system == "windows" else "darkly-go")
    if DRY:
        run(["go", "build", "-o", binary, "."], fatal=False, cwd=go_dir)
    elif shutil.which("go"):
        if run(["go", "build", "-o", binary, "."], fatal=False, cwd=go_dir):
            say("darkly-go compilado OK.", "g")
    else:
        say("Go no instalado; el menú Python funciona igual como respaldo.", "y")

    say("\nListo. Ejecuta: python darkly.py", "g")
    say("Nota: traceroute puede pedir root en algunos modos.", "c")


if __name__ == "__main__":
    main()
