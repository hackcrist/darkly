"""System-related activities - local host info only."""
import os
import platform
import shutil
import socket


def sys_info() -> dict:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": socket.gethostname(),
        "python": platform.python_version(),
        "cwd": os.getcwd(),
    }


def disk_usage(path: str = ".") -> dict:
    total, used, free = shutil.disk_usage(path)
    return {"path": os.path.abspath(path), "total_GB": round(total / 1e9, 2),
            "used_GB": round(used / 1e9, 2), "free_GB": round(free / 1e9, 2)}


def try_psutil_stats() -> dict:
    try:
        import psutil
        import datetime as _dt
        boot = _dt.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.3),
            "cpu_nucleos": psutil.cpu_count(logical=True),
            "memory_percent": psutil.virtual_memory().percent,
            "boot_time": boot,
        }
    except ImportError:
        return {"nota": "Instala psutil para ver CPU/RAM en vivo: pip install psutil"}


def file_hash(path: str, algo: str = "sha256") -> dict:
    """Calcula el hash de un archivo local por partes (verificar descargas / integridad)."""
    import hashlib as _hl
    algo = algo.lower().replace("-", "")
    if algo not in _hl.algorithms_available:
        raise ValueError("Algoritmo no soportado")
    h = _hl.new(algo)
    size = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
            size += len(chunk)
            if size > 500 * 1024 * 1024:
                raise ValueError("Archivo muy grande (>500MB) para esta herramienta educativa")
    return {"path": os.path.abspath(path), "algo": algo,
            "hex": h.hexdigest(), "bytes": size}


def get_uptime() -> str:
    import time
    try:
        import psutil
        boot = psutil.boot_time()
        secs = int(time.time() - boot)
    except ImportError:
        # Alternativa en Linux
        try:
            with open("/proc/uptime") as f:
                secs = int(float(f.read().split()[0]))
        except Exception:
            return "Instala psutil o ejecútalo en Linux para ver el uptime"
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"


def list_processes(limit: int = 15) -> list[dict]:
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent"]):
            try:
                procs.append(p.info)
            except Exception:
                continue
            if len(procs) >= limit:
                break
        return procs
    except ImportError:
        # Fallback: ps / tasklist
        import subprocess as _sp
        import platform as _pf
        try:
            if _pf.system().lower() == "windows":
                out = _sp.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=10)
                return [{"raw": line} for line in (out.stdout or "").splitlines()[:limit]]
            out = _sp.run(["ps", "-eo", "pid,comm,pcpu", "--sort=-pcpu"], capture_output=True, text=True, timeout=10)
            return [{"raw": line} for line in (out.stdout or "").splitlines()[: limit + 1]]
        except Exception as e:
            return [{"error": str(e)}]


def check_permissions(path: str) -> dict:
    st = os.stat(path)
    return {"path": os.path.abspath(path), "mode_octal": oct(st.st_mode & 0o777),
            "uid": getattr(st, "st_uid", "n/a"), "gid": getattr(st, "st_gid", "n/a"),
            "size": st.st_size}


def tail_log(path: str, lines: int = 20) -> list[str]:
    if not 1 <= lines <= 200:
        raise ValueError("lines must be 1-200")
    with open(path, encoding="utf-8", errors="replace") as f:
        data = f.readlines()
    return [l.rstrip("\n") for l in data[-lines:]]


def file_hash_verify(path: str, esperado: str, algo: str = "sha256") -> dict:
    """Precisión real: compara el hash calculado contra el esperado (verificación de descargas)."""
    calc = file_hash(path, algo)
    esp = esperado.strip().lower().split()[0]  # admite formato 'hash  nombre'
    ok = calc["hex"].lower() == esp
    return {"path": calc["path"], "algo": calc["algo"], "calculado": calc["hex"],
            "esperado": esp, "coincide": ok,
            "resultado": "COINCIDE - archivo integro" if ok else "NO COINCIDE - archivo alterado o corrupto"}
