"""Security / defensive tools - educational only. No exploitation payloads."""
import hashlib
import re
import secrets
import string
import urllib.request


COMMON_PORTS = {
    21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
    80: "http", 110: "pop3", 143: "imap", 443: "https",
    3306: "mysql", 3389: "rdp", 5900: "vnc", 8080: "http-alt",
}

HASH_PATTERNS = [
    ("MD5 (32 hex)", re.compile(r"^[a-fA-F0-9]{32}$")),
    ("SHA-1 (40 hex)", re.compile(r"^[a-fA-F0-9]{40}$")),
    ("SHA-256 (64 hex)", re.compile(r"^[a-fA-F0-9]{64}$")),
    ("SHA-512 (128 hex)", re.compile(r"^[a-fA-F0-9]{128}$")),
    ("bcrypt ($2a/$2b/$2y$)", re.compile(r"^\$2[aby]\$\d{2}\$.{53}$")),
]


def identify_hash(h: str) -> list[str]:
    h = h.strip()
    return [name for name, rx in HASH_PATTERNS if rx.match(h)] or ["Formato desconocido"]


def hash_text(text: str, algo: str = "sha256") -> str:
    algo = algo.lower().replace("-", "")
    if algo not in hashlib.algorithms_available:
        raise ValueError("Algoritmo no soportado. Usa p. ej. sha256, sha1, md5")
    return hashlib.new(algo, text.encode()).hexdigest()


def password_strength(password: str) -> dict:
    score = 0
    feedback = []
    if len(password) >= 12:
        score += 2
    elif len(password) >= 8:
        score += 1
    else:
        feedback.append("Usa al menos 12 caracteres.")
    if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password):
        score += 1
    else:
        feedback.append("Mezcla mayúsculas y minúsculas.")
    if re.search(r"\d", password):
        score += 1
    else:
        feedback.append("Agrega números.")
    if re.search(r"[^A-Za-z0-9]", password):
        score += 1
    else:
        feedback.append("Agrega símbolos.")
    if len(set(password)) < len(password) * 0.6:
        feedback.append("Evita caracteres repetidos.")
    else:
        score += 1
    level = "Muy débil" if score <= 2 else "Débil" if score <= 3 else "Aceptable" if score <= 4 else "Fuerte" if score <= 5 else "Muy fuerte"
    return {"puntuación": score, "nivel": level, "recomendaciones": feedback}


def generate_password(length: int = 16) -> str:
    if not 8 <= length <= 64:
        raise ValueError("La longitud debe ser 8-64")
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(alphabet) for _ in range(length))


def check_security_headers(url: str, timeout: int = 10) -> dict:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    req = urllib.request.Request(url, headers={"User-Agent": "Darkly-Tools/1.0 (educational)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        headers = dict(r.headers)
    wanted = ["Content-Security-Policy", "Strict-Transport-Security",
              "X-Content-Type-Options", "X-Frame-Options",
              "Referrer-Policy", "Permissions-Policy"]
    return {h: headers.get(h, "MISSING") for h in wanted}


_range_cache: dict[str, str] = {}
_MAX_RANGE_CACHE = 256


def _fetch_range(prefix: str, timeout: int = 10) -> str:
    if prefix in _range_cache:
        return _range_cache[prefix]
    req = urllib.request.Request(
        f"https://api.pwnedpasswords.com/range/{prefix}",
        headers={"User-Agent": "Darkly-Tools/2.0 (educativo)", "Add-Padding": "true"})
    import ssl as _ssl
    try:
        import certifi
        ctx = _ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = _ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        body = r.read().decode()
    if len(_range_cache) >= _MAX_RANGE_CACHE:
        _range_cache.pop(next(iter(_range_cache)), None)
    _range_cache[prefix] = body
    return body


def audit_password(password: str, timeout: int = 10) -> dict:
    """Afinado: fortaleza + filtración en una sola pasada."""
    fuerza = password_strength(password)
    brecha = check_password_breach(password, timeout)
    if "error" in brecha:
        veredicto = f"Fortaleza {fuerza['nivel']}; filtración no verificable ({brecha['error']})"
    elif brecha["comprometida"]:
        veredicto = (f"NO USAR: filtrada {brecha['veces_vista']} veces aunque su fortaleza sea {fuerza['nivel']}. "
                     "Genera una nueva con la opción 4.")
    elif fuerza["nivel"] in ("Fuerte", "Muy fuerte"):
        veredicto = "OK: fuerte y sin filtraciones conocidas."
    else:
        veredicto = f"Mejorable: {fuerza['nivel']} y sin filtraciones, pero hazla más larga/única."
    return {"fortaleza": fuerza, "filtracion": brecha, "veredicto": veredicto}


def check_password_breach(password: str, timeout: int = 10) -> dict:
    """Verifica si la contraseña apareció en filtraciones (HaveIBeenPwned, k-anonymity).

    Privado: solo se envían los primeros 5 chars del SHA-1, nunca la contraseña.
    """
    import hashlib as _hl
    if not password:
        raise ValueError("Contraseña vacía")
    sha1 = _hl.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        body = _fetch_range(prefix, timeout)
    except Exception as e:
        return {"error": f"No se pudo consultar HIBP: {e}. Revisa tu conexión."}
    count = 0
    for line in body.splitlines():
        if ":" not in line:
            continue
        suf, n = line.split(":", 1)
        if suf.strip().upper() == suffix:
            count = int(n.strip())
            break
    if count > 0:
        return {"comprometida": True, "veces_vista": count,
                "resultado": f"COMPROMETIDA: vista {count} veces en filtraciones. Cámbiala ya y no la reuses."}
    return {"comprometida": False, "veces_vista": 0,
            "resultado": "No aparece en filtraciones conocidas. Igual usa contraseña única y larga."}


SUSPICIOUS_TLDS = {"tk", "ml", "ga", "cf", "gq", "zip", "mov", "click", "link"}
SUSPICIOUS_WORDS = ("login", "verify", "secure", "account", "update", "free",
                    "prize", "winner", "paypal", "bank", "gift")


def scan_url(url: str) -> dict:
    """Análisis heurístico defensivo de URL. Sin payloads, sin descargar nada. Solo análisis."""
    import urllib.parse
    original = url.strip()
    if not original:
        raise ValueError("URL vacía")
    if "://" not in original:
        original = "http://" + original
    try:
        p = urllib.parse.urlparse(original)
    except Exception as e:
        raise ValueError(f"URL no válida: {e}")
    host = (p.hostname or "").lower().rstrip(".")
    findings: list[str] = []
    risk = 0
    if not host:
        return {"url": original, "riesgo": 100, "nivel": "Alto", "hallazgos": ["No se encontró un host válido"]}
    if "@" in original.split("://", 1)[-1].split("/")[0] or "@" in (p.netloc or ""):
        findings.append("'@' en la autoridad — posible truco de redirección")
        risk += 25
    if p.scheme == "http":
        findings.append("Usa HTTP sin cifrado (sin TLS)")
        risk += 10
    try:
        import ipaddress as _ip
        _ip.ip_address(host.strip("[]"))
        findings.append("El host es una IP cruda, no un dominio")
        risk += 20
    except ValueError:
        pass
    if host.startswith("xn--") or "xn--" in host:
        findings.append("Punycode (xn--) — posible suplantación homógrafa/IDN")
        risk += 20
    parts = host.strip("[]").split(".")
    if len(parts) > 4:
        findings.append(f"Muchos subdominios ({len(parts)}) — posible suplantación")
        risk += 10
    if parts and parts[-1] in SUSPICIOUS_TLDS:
        findings.append(f"TLD sospechoso: .{parts[-1]}")
        risk += 15
    low = original.lower()
    main_domain = ".".join(parts[-2:]) if len(parts) >= 2 else host
    for w in SUSPICIOUS_WORDS:
        if w in low:
            if w in ("paypal", "bank") and (main_domain == f"{w}.com" or main_domain.endswith(f".{w}.com") or main_domain.startswith(f"{w}.")):
                continue
            findings.append(f"Palabra '{w}' muy usada en phishing")
            risk += 5
            break
    if len(original) > 150:
        findings.append("URL muy larga — suele usarse para ocultar el host real")
        risk += 10
    if p.port and p.port not in (80, 443):
        findings.append(f"Puerto inusual: {p.port}")
        risk += 10
    risk = min(risk, 100)
    level = "Bajo" if risk < 30 else "Medio" if risk < 60 else "Alto"
    if not findings:
        findings.append("Sin señales obvias (igual verifica el remitente/contexto)")
    return {"url": original, "host": host, "esquema": p.scheme or "?", "riesgo": risk,
            "nivel": level, "hallazgos": findings}
