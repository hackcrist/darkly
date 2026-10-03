"""Networking tools - educational only. Use only on hosts you own or are authorized to test."""
import os
import socket
import subprocess
import ipaddress
import concurrent.futures


def resolve_host(host: str) -> str:
    try:
        return socket.gethostbyname(host)
    except socket.gaierror as e:
        return f"[!] Falló la resolución DNS: {e}"


def dns_lookup(host: str, timeout: int = 8) -> dict:
    """DNS preciso: primero sistema, si falla usa DoH (Cloudflare) como respaldo."""
    result: dict = {"host": host}
    try:
        result["ip"] = socket.gethostbyname(host)
        result["fqdn"] = socket.getfqdn(host)
        try:
            result["addr_info"] = socket.getaddrinfo(host, None)[:3]
        except Exception:
            result["addr_info"] = []
        result["fuente"] = "sistema"
        return result
    except socket.gaierror as e:
        result["error_sistema"] = str(e)
    # Respaldo DoH (HTTPS = casi nunca bloqueado)
    try:
        import json as _json
        import urllib.request as _req
        import urllib.parse as _parse
        import ssl as _ssl
        try:
            import certifi
            _ctx = _ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            _ctx = _ssl.create_default_context()
        url = "https://one.one.one.one/dns-query?name=" + _parse.quote(host) + "&type=A"
        rq = _req.Request(url, headers={"Accept": "application/dns-json",
                                        "User-Agent": "Darkly-Tools/1.0 (educativo)"})
        with _req.urlopen(rq, timeout=timeout, context=_ctx) as r:
            data = _json.loads(r.read().decode())
        answers = [a["data"] for a in data.get("Answer", []) if a.get("type") in (1, 28)]
        if answers:
            result["ip"] = answers[0]
            result["todas_ips"] = answers
            result["fuente"] = "DoH-cloudflare"
            result.pop("error_sistema", None)
        else:
            result["error"] = f"Sin respuesta DNS ni por DoH. Detalle: {result.get('error_sistema')}"
    except Exception as e2:
        result["error"] = f"DNS falló (sistema + DoH): {result.get('error_sistema')} / DoH: {e2}"
    return result


def check_port(host: str, port: int, timeout: float = 1.0) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0


def port_scan(host: str, ports: list[int], timeout: float = 1.0, workers: int = 50) -> dict[int, bool]:
    ip = resolve_host(host)
    if ip.startswith("[!]"):
        return {"error": ip}  # type: ignore
    # Si dieron hostname, resolve_host devuelve IP; si dieron IP directa úsala
    try:
        ipaddress.ip_address(host.strip())
        ip = host.strip()
    except ValueError:
        pass
    results: dict[int, bool] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        fut = {ex.submit(check_port, ip, p, timeout): p for p in ports}
        for f in concurrent.futures.as_completed(fut):
            try:
                results[fut[f]] = f.result()
            except Exception:
                results[fut[f]] = False
    return results


def banner_grab(host: str, port: int, timeout: float = 3.0) -> str:
    """Precisión real: conecta y lee el banner del servicio (sin exploits)."""
    try:
        port = int(port)
        if not (1 <= port <= 65535):
            return "puerto fuera de rango (1-65535)"
    except (ValueError, TypeError):
        return "puerto no válido"
    ip = host.strip()
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        ip = resolve_host(host)
        if ip.startswith("[!]"):
            return ip
    try:
        with socket.create_connection((ip, port), timeout=timeout) as s:
            s.settimeout(timeout)
            # HTTP: pide cabecera para identificar; otros: solo lee banner inicial
            if port in (80, 8080, 8000):
                s.sendall(b"HEAD / HTTP/1.0\r\nHost: x\r\n\r\n")
            elif port == 443:
                return "443/tcp: TLS (banner cifrado, usa 'Cabeceras de seguridad' por HTTPS)"
            try:
                data = s.recv(512)
            except socket.timeout:
                return "abierto (sin banner, timeout leyendo)"
            if not data:
                return "abierto (sin banner)"
            txt = data.decode(errors="replace").strip().splitlines()
            raw_line = txt[0] if txt else ""
            clean_line = "".join(c for c in raw_line if (ord(c) >= 32 and ord(c) != 127) or c in "\t")
            return (clean_line if clean_line else "abierto (banner vacío)")[:200]
    except (socket.timeout, ConnectionRefusedError):
        return "cerrado/filtrado"
    except Exception as e:
        return f"abierto? (error leyendo banner: {e})"


def _safe_host(host: str) -> str:
    """Solo letras, números, puntos, guiones y : (IPv6). Evita inyección al usar cmd."""
    import re
    host = validate_target(host)
    if not re.match(r"^[A-Za-z0-9.\-:]+$", host):
        raise ValueError("Host no válido (solo letras, números, puntos, guiones)")
    return host


_cached_oem_cp = None


def _decode_console(data: bytes) -> str:
    """Decodifica salida de ping/tracert: UTF-8 si es válida, si no codepage OEM."""
    global _cached_oem_cp
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    if os.name == "nt":
        if _cached_oem_cp:
            return data.decode(_cached_oem_cp, errors="replace")
        try:
            import ctypes
            cp = ctypes.windll.kernel32.GetOEMCP()
            _cached_oem_cp = f"cp{cp}"
            return data.decode(_cached_oem_cp, errors="replace")
        except Exception:
            try:
                out = subprocess.run(["cmd", "/c", "chcp"], capture_output=True, timeout=5)
                import re as _re
                nums = _re.findall(r"\d+", (out.stdout or b"").decode(errors="replace"))
                cp = nums[-1] if nums else "850"
                _cached_oem_cp = f"cp{cp}"
                return data.decode(_cached_oem_cp, errors="replace")
            except Exception:
                _cached_oem_cp = "cp850"
                return data.decode("cp850", errors="replace")
    return data.decode(errors="replace")


def ping_host(host: str, count: int = 2, timeout: int = 2) -> str:
    # Ping multiplataforma, sin raw sockets
    import platform
    host = _safe_host(host)
    count, timeout = int(count), int(timeout)
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=timeout * count + 5)
        txt = _decode_console(out.stdout) or _decode_console(out.stderr)
        return txt
    except Exception as e:
        return f"[!] falló el ping: {e}"


def parse_ports(port_str: str) -> list[int]:
    """Convierte '22,80,443' o '1-1024' en lista de puertos (máx 1024)."""
    ports: set[int] = set()
    for part in port_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            try:
                start, end = int(a.strip()), int(b.strip())
            except ValueError:
                raise ValueError(f"Rango numérico no válido: {part}")
            if not (1 <= start <= 65535 and 1 <= end <= 65535 and start <= end):
                raise ValueError(f"Rango no válido: {part}")
            if end - start > 1024:
                raise ValueError("Rango muy grande (máx 1024 puertos por escaneo)")
            ports.update(range(start, end + 1))
        else:
            try:
                p = int(part)
            except ValueError:
                raise ValueError(f"Puerto numérico no válido: {part}")
            if not 1 <= p <= 65535:
                raise ValueError(f"Puerto no válido: {part}")
            ports.add(p)
        if len(ports) > 1024:
            raise ValueError("Demasiados puertos en total (máx 1024 puertos por escaneo)")
    return sorted(ports)


def validate_target(host: str) -> str:
    host = host.strip()
    if not host:
        raise ValueError("Host vacío")
    # Limpia esquemas (http://, https://), rutas y puertos si el usuario pegó una URL
    if "://" in host:
        host = host.split("://", 1)[1]
    host = host.split("/")[0].split(":")[0].strip()
    if not host:
        raise ValueError("Host no válido tras limpiar la URL")
    return host


def traceroute(host: str, max_hops: int = 20, timeout: int = 2) -> str:
    """Traceroute del sistema (educativo). Usa tracert en Windows, traceroute en Linux."""
    import platform
    import shutil
    host = _safe_host(host)
    system = platform.system().lower()
    if system == "windows":
        cmd = ["tracert", "-d", "-h", str(int(max_hops)), "-w", str(int(timeout) * 1000), host]
    else:
        bin_path = shutil.which("traceroute")
        if not bin_path:
            return "[!] 'traceroute' no encontrado. Instálalo: sudo apt install traceroute"
        cmd = [bin_path, "-n", "-m", str(max_hops), "-w", str(timeout), host]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=max_hops * (timeout + 1) + 10)
        return _decode_console(out.stdout) or _decode_console(out.stderr) or "[!] Sin salida"
    except subprocess.TimeoutExpired:
        return "[!] traceroute agotó el tiempo (prueba con menos saltos)"
    except Exception as e:
        return f"[!] falló traceroute: {e}"


def subnet_info(cidr: str) -> dict:
    """Calcula datos de red desde un CIDR como 192.168.1.0/24 o 10.0.0.5/16 de forma segura y matemática."""
    cidr = cidr.strip()
    try:
        net = ipaddress.ip_network(cidr, strict=False)
    except ValueError as e:
        raise ValueError(f"CIDR no válido '{cidr}': {e}")
    total = net.num_addresses
    if net.version == 4:
        if net.prefixlen == 32:
            usable = 1
            first_host = str(net.network_address)
            last_host = str(net.network_address)
        elif net.prefixlen == 31:
            usable = 2
            first_host = str(net.network_address)
            last_host = str(net.network_address + 1)
        else:
            usable = max(total - 2, 0)
            first_host = str(net.network_address + 1) if usable > 0 else "n/a"
            last_host = str(net.broadcast_address - 1) if usable > 0 else "n/a"
        broadcast = str(net.broadcast_address)
    else:
        usable = total
        first_host = str(net.network_address)
        last_host = "n/a (IPv6)"
        broadcast = "n/a (IPv6)"
    return {
        "network": str(net.network_address),
        "broadcast": broadcast,
        "netmask": str(net.netmask),
        "prefix": net.prefixlen,
        "total_addresses": total,
        "usable_hosts": usable,
        "first_host": first_host,
        "last_host": last_host,
        "version": f"IPv{net.version}",
    }
