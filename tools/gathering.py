"""Information gathering - passive / OSINT helpers. Educational only."""
import json
import re
import socket
import urllib.request
import urllib.parse


def _ssl_ctx():
    import ssl as _ssl
    try:
        import certifi
        return _ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return _ssl.create_default_context()


def _get_json(url: str, timeout: int = 12) -> dict | list:
    rq = urllib.request.Request(url, headers={"User-Agent": "Darkly-Tools/2.0 (educativo)",
                                              "Accept": "application/json"})
    with urllib.request.urlopen(rq, timeout=timeout, context=_ssl_ctx()) as r:
        return json.loads(r.read().decode())


def _doh(domain: str, rtype: str, timeout: int = 8) -> list[str]:
    # one.one.one.one primero: es el único DoH con certificado válido
    # en redes con filtro TLS (otros endpoints pueden ser interceptados).
    endpoints = ("https://one.one.one.one/dns-query?name=",
                 "https://cloudflare-dns.com/dns-query?name=")
    ultimo = ""
    for base in endpoints:
        try:
            url = base + urllib.parse.quote(domain) + f"&type={rtype}"
            rq = urllib.request.Request(url, headers={"Accept": "application/dns-json",
                                                      "User-Agent": "Darkly-Tools/2.0 (educativo)"})
            with urllib.request.urlopen(rq, timeout=timeout, context=_ssl_ctx()) as r:
                data = json.loads(r.read().decode())
            ans = [a.get("data", "") for a in data.get("Answer", []) if a.get("data")]
            if ans:
                return ans
            ultimo = "sin respuesta"
        except Exception as e:
            ultimo = str(e)[:100]
            continue
    raise RuntimeError(f"DoH falló en todos los endpoints: {ultimo}")


def _clean_domain(d: str) -> str:
    d = d.strip().lower()
    d = re.sub(r"^https?://", "", d).split("/")[0].split(":")[0]
    if d.startswith("www."):
        d = d[4:]
    if not re.match(r"^(?!-)[a-z0-9.-]+\.[a-z]{2,}$", d):
        raise ValueError(f"'{d}' no parece un dominio válido (ej. google.com)")
    return d


def dns_records(domain: str, timeout: int = 8) -> dict:
    """Registros A, MX, TXT, NS vía DoH (sin dependencias)."""
    d = _clean_domain(domain)
    out: dict = {"dominio": d}
    for rt in ("A", "MX", "TXT", "NS"):
        try:
            out[rt] = _doh(d, rt, timeout) or ["(sin registros)"]
        except Exception as e:
            out[rt] = [f"error: {e}"]
    return out


def _hackertarget_subs(domain: str, timeout: int = 10) -> set[str]:
    """Respaldo gratis (HackerTarget hostsearch): líneas 'host,ip'."""
    rq = urllib.request.Request(
        f"https://api.hackertarget.com/hostsearch/?q={urllib.parse.quote(domain)}",
        headers={"User-Agent": "Darkly-Tools/2.0 (educativo)"})
    with urllib.request.urlopen(rq, timeout=timeout, context=_ssl_ctx()) as r:
        body = r.read().decode()
    subs: set[str] = set()
    for line in body.splitlines():
        host = line.split(",")[0].strip().lower().lstrip("*.")
        if host and (host == domain or host.endswith("." + domain)):
            subs.add(host)
    return subs


def subdomains_crtsh(domain: str, timeout: int = 15, limit: int = 50) -> dict:
    """Subdominios vía Certificate Transparency (crt.sh, gratis, pasivo)."""
    d = _clean_domain(domain)
    url = f"https://crt.sh/?q=%25.{urllib.parse.quote(d)}&output=json"
    ultimo = ""
    data = None
    for intento in range(3):
        try:
            data = _get_json(url, timeout)
            break
        except Exception as e:
            ultimo = str(e)[:120]
            if intento < 2:
                import time as _t
                _t.sleep(3)
    if data is None:
        # Respaldo gratis: HackerTarget hostsearch
        try:
            fb = _hackertarget_subs(d, timeout)
            if fb:
                ordered = sorted(fb)[:limit]
                return {"dominio": d, "total": len(fb), "mostrando": len(ordered),
                        "subdominios": ordered, "fuente": "hackertarget (respaldo)"}
        except Exception as e2:
            ultimo += f" / HT: {e2}"
        return {"dominio": d, "error": f"crt.sh falló tras 3 intentos: {ultimo}. Reintenta más tarde."}
    subs: set[str] = set()
    if isinstance(data, list):
        for entry in data:
            nv = str(entry.get("name_value", ""))
            for line in nv.splitlines():
                s = line.strip().lower().lstrip("*.")
                if s and (s == d or s.endswith("." + d)):
                    subs.add(s)
    ordered = sorted(subs)[:limit]
    return {"dominio": d, "total": len(subs), "mostrando": len(ordered), "subdominios": ordered}


def github_profile(user: str, timeout: int = 10) -> dict:
    """Perfil público GitHub (API sin key, 60 req/hora)."""
    u = user.strip().lstrip("@")
    if not re.match(r"^[A-Za-z0-9-]{1,39}$", u):
        raise ValueError("Usuario GitHub no válido")
    try:
        data = _get_json(f"https://api.github.com/users/{urllib.parse.quote(u)}", timeout)
    except Exception as e:
        return {"error": f"GitHub API falló: {e}"}
    if isinstance(data, dict) and data.get("message") == "Not Found":
        return {"usuario": u, "error": "No existe ese usuario en GitHub"}
    keep = ("login", "name", "company", "blog", "location", "email", "bio",
            "public_repos", "followers", "following", "created_at", "html_url")
    return {k: data.get(k, "-") for k in keep}


def _norm_geo(data: dict) -> dict:
    """Normaliza ipwho.is (latitude/longitude/connection) al esquema común."""
    if isinstance(data, dict) and "latitude" in data and "lat" not in data:
        conn = data.get("connection") or {}
        data["lat"] = data.get("latitude")
        data["lon"] = data.get("longitude")
        data["query"] = data.get("ip", data.get("query"))
        data["org"] = conn.get("org") or conn.get("isp") or data.get("org")
        data["isp"] = conn.get("isp") or data.get("isp")
    return data


def public_ip_info(timeout: int = 10) -> dict:
    """Multi-fuente con respaldo: ip-api -> ipapi.co -> ipwho.is."""
    import json as _json
    import urllib.request as _req
    fuentes = [
        "http://ip-api.com/json/?fields=status,message,country,regionName,city,query,org,isp",
        "https://ipapi.co/json/",
        "https://ipwho.is/json/",
    ]
    ultimo_error = ""
    for url in fuentes:
        try:
            rq = _req.Request(url, headers={"User-Agent": "Darkly-Tools/1.0 (educativo)"})
            with _req.urlopen(rq, timeout=timeout, context=_ssl_ctx()) as r:
                data = _norm_geo(_json.loads(r.read().decode()))
            data["fuente"] = url
            return data
        except Exception as e:
            ultimo_error = f"{url}: {e}"
    return {"error": f"Todas las fuentes fallaron. {ultimo_error}. Revisa tu internet/DNS."}


def ip_lookup(ip: str, timeout: int = 10) -> dict:
    ip = ip.strip()
    import ipaddress as _ip
    try:
        _ip.ip_address(ip)
    except ValueError:
        return {"error": f"'{ip}' no es una IP válida (ej. 8.8.8.8)"}
    import json as _json
    import urllib.request as _req
    fuentes = [
        f"http://ip-api.com/json/{urllib.parse.quote(ip)}?fields=status,message,country,regionName,city,lat,lon,org,isp,query",
        f"https://ipapi.co/{urllib.parse.quote(ip)}/json/",
        f"https://ipwho.is/{urllib.parse.quote(ip)}",
    ]
    ultimo_error = ""
    for url in fuentes:
        try:
            rq = _req.Request(url, headers={"User-Agent": "Darkly-Tools/1.0 (educativo)"})
            with _req.urlopen(rq, timeout=timeout, context=_ssl_ctx()) as r:
                data = _norm_geo(_json.loads(r.read().decode()))
            data["fuente"] = url
            return data
        except Exception as e:
            ultimo_error = f"{url}: {e}"
    return {"error": f"Todas las fuentes fallaron. {ultimo_error}"}


def http_headers(url: str, timeout: int = 10) -> dict:
    url = url.strip()
    if not url:
        raise ValueError("URL vacía")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    import ssl as _ssl
    try:
        import certifi
        ctx = _ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = _ssl.create_default_context()
    # 1) Intento HEAD rápido
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": "Darkly-Tools/1.0 (educativo)"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                h = dict(r.headers)
                h["_url_final"] = r.geturl()
                h["_metodo"] = method
                return h
        except Exception as e:
            ultimo = e
            continue
    return {"error": f"No se pudo obtener cabeceras: {ultimo}. Prueba con http:// en vez de https://."}


def rdap_lookup(query: str, timeout: int = 12) -> dict:
    """RDAP por HTTPS (puerto 443): reemplazo moderno y preciso de WHOIS (que falla si bloquean puerto 43)."""
    import json as _json
    import urllib.request as _req
    import urllib.parse as _parse
    import ipaddress as _ip
    q = query.strip().lower().rstrip(".")
    if not q:
        raise ValueError("Consulta vacía")
    try:
        _ip.ip_address(q)
        url = f"https://rdap.db.ripe.net/ip/{_parse.quote(q)}"
    except ValueError:
        if "." in q:
            # Dominio: usa RDAP de Verisign para .com/.net, si no IANA bootstrap
            if q.endswith((".com", ".net")):
                url = f"https://rdap.verisign.com/com/v1/domain/{_parse.quote(q)}"
            else:
                url = f"https://data.iana.org/rdap/domain/{_parse.quote(q)}"
        else:
            raise ValueError("Dame un dominio (ej. google.com) o IP (ej. 8.8.8.8)")
    try:
        rq = _req.Request(url, headers={"Accept": "application/json", "User-Agent": "Darkly-Tools/1.0 (educativo)"})
        with _req.urlopen(rq, timeout=timeout, context=_ssl_ctx()) as r:
            data = _json.loads(r.read().decode())
        # Resumen preciso
        resumen = {"fuente": url, "nombre": data.get("name") or data.get("ldhName"),
                   "estado": data.get("status"), "registros": len(data.get("entities", []))}
        # Fecha de creación/expiración si existe
        for ev in data.get("events", []):
            if ev.get("eventAction") in ("registration", "expiration"):
                resumen[ev["eventAction"]] = ev.get("eventDate")
        return resumen
    except Exception as e:
        return {"error": f"RDAP falló: {e}. Prueba con otro dominio o revisa tu conexión."}


def reverse_dns(ip: str, timeout: int = 8) -> str:
    """PTR preciso: valida la IP, explica privadas/reservadas y usa respaldo DoH."""
    import ipaddress as _ip
    ip = ip.strip().strip("[]")
    try:
        addr = _ip.ip_address(ip)
    except ValueError:
        return f"[!] '{ip}' no es una IP válida (ej. 8.8.8.8)"
    if addr.is_loopback:
        return "localhost (loopback, sin PTR público)"
    if addr.is_private:
        return "IP privada RFC1918 (sin PTR público; solo tu router la conoce)"
    if addr.is_reserved or addr.is_multicast or addr.is_link_local or addr.is_unspecified:
        return "IP reservada/especial (sin PTR público esperado)"
    # 1) Sistema
    try:
        nombre = socket.gethostbyaddr(ip)[0]
        return f"{nombre} (fuente: sistema)"
    except Exception as e1:
        ultimo = str(e1)
    # 2) Respaldo DoH: consulta PTR (in-addr.arpa / ip6.arpa)
    try:
        if addr.version == 4:
            rev = ".".join(reversed(ip.split("."))) + ".in-addr.arpa"
        else:
            rev = _ip.ip_address(ip).reverse_pointer
        import json as _json
        import urllib.request as _req
        import urllib.parse as _parse
        for base in ("https://one.one.one.one/dns-query?name=",
                     "https://cloudflare-dns.com/dns-query?name=",
                     "https://dns.google/resolve?name="):
            try:
                url = base + _parse.quote(rev) + "&type=PTR"
                rq = _req.Request(url, headers={"Accept": "application/dns-json",
                                                "User-Agent": "Darkly-Tools/1.0 (educativo)"})
                with _req.urlopen(rq, timeout=timeout, context=_ssl_ctx()) as r:
                    data = _json.loads(r.read().decode())
                for a in data.get("Answer", []):
                    d = a.get("data", "").rstrip(".")
                    if d:
                        return f"{d} (fuente: DoH)"
            except Exception:
                continue
    except Exception as e2:
        ultimo += f" / DoH: {e2}"
    return f"[!] Sin registro PTR para {ip} (el dueño no creó reverso). Detalle: {ultimo}"


def whois_lookup(query: str, timeout: int = 10) -> str:
    """Cliente WHOIS mínimo (educativo). Consulta whois.iana.org y sigue la referencia."""
    query = query.strip().lower()
    if not query:
        raise ValueError("Consulta vacía")
    # Seguridad básica: solo dominio o IP
    import re as _re
    if not _re.match(r"^[a-z0-9.\-:]+$", query):
        raise ValueError("Caracteres no válidos en dominio/IP")

    def _ask(server: str, q: str) -> str:
        with socket.create_connection((server, 43), timeout=timeout) as s:
            s.sendall((q + "\r\n").encode())
            data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 16384:
                    break
        return data.decode(errors="replace")

    try:
        resp = _ask("whois.iana.org", query)
    except Exception as e:
        return f"[!] WHOIS falló (el puerto 43 puede estar bloqueado): {e}"
    # Follow referral if present
    refer = None
    for line in resp.splitlines():
        if line.lower().startswith("refer:"):
            refer = line.split(":", 1)[1].strip()
            break
        if line.lower().startswith("whois:"):
            refer = line.split(":", 1)[1].strip()
            break
    if refer:
        try:
            resp += f"\n\n--- referencia: {refer} ---\n" + _ask(refer, query)
        except Exception as e:
            resp += f"\n[!] referencia {refer} falló: {e}"
    return resp[:8000]
