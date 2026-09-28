"""Búsqueda pasiva de nombre de usuario en sitios públicos (OSINT educativo).

Solo consulta páginas públicas, sin logins ni intentos de acceso.
Los sitios con muro de login/JS se marcan como 'indicio', no confirmación.
"""
import os
import re
import time
import datetime
import urllib.request
import concurrent.futures

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def _ssl_context():
    """Usa certifi si está instalado (corrige CERTIFICATE_VERIFY_FAILED en Windows)."""
    import ssl as _ssl
    try:
        import certifi
        return _ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return _ssl.create_default_context()

# (nombre, plantilla_url, nivel) nivel: "firme" = 404 fiable, "indicio" = JS/login-wall
SITES: list[tuple[str, str, str]] = [
    ("GitHub", "https://github.com/{u}", "firme"),
    ("GitLab", "https://gitlab.com/{u}", "firme"),
    ("PyPI", "https://pypi.org/user/{u}/", "firme"),
    ("npm", "https://www.npmjs.com/~{u}", "firme"),
    ("DockerHub", "https://hub.docker.com/u/{u}", "firme"),
    ("Reddit", "https://www.reddit.com/user/{u}/", "firme"),
    ("Twitch", "https://www.twitch.tv/{u}", "firme"),
    ("Pinterest", "https://www.pinterest.com/{u}/", "firme"),
    ("Vimeo", "https://vimeo.com/{u}", "firme"),
    ("SoundCloud", "https://soundcloud.com/{u}", "indicio"),
    ("Chess.com", "https://www.chess.com/member/{u}", "firme"),
    ("Telegram", "https://t.me/{u}", "indicio"),
    ("Medium", "https://medium.com/@{u}", "indicio"),
    ("TikTok", "https://www.tiktok.com/@{u}", "indicio"),
    ("Instagram", "https://www.instagram.com/{u}/", "indicio"),
    ("X", "https://x.com/{u}", "indicio"),
    ("YouTube", "https://www.youtube.com/@{u}", "indicio"),
]

NOT_FOUND = (
    "not found", "page not found", "nobody on reddit",
    "doesn't exist", "couldn't find", "no hemos encontrado",
    "usuario no encontrado", "this account doesn't exist",
    "sorry, this page isn't available",
)


def validate_username(u: str) -> str:
    u = u.strip().lstrip("@")
    if not re.match(r"^[A-Za-z0-9._-]{2,30}$", u):
        raise ValueError("Usuario no válido: usa 2-30 caracteres (letras, números, . _ -)")
    return u


def _check_npm(u: str, timeout: int = 10) -> tuple[str, str, str]:
    """npm bloquea scraping (403 Cloudflare). Usa su API pública de registry."""
    import json as _json
    import urllib.parse as _parse
    url = "https://registry.npmjs.org/-/v1/search?text=maintainer:" + _parse.quote(u) + "&size=1"
    try:
        req = urllib.request.Request(url, headers={**UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as r:
            data = _json.loads(r.read().decode())
        total = data.get("total", 0)
        if total and total > 0:
            return "npm", f"posible perfil ({total} paquetes)", f"https://www.npmjs.com/~{u}"
        return "npm", "sin paquetes (puede existir sin publicar)", f"https://www.npmjs.com/~{u}"
    except Exception as e:
        return "npm", f"error: {str(e)[:80]}", f"https://www.npmjs.com/~{u}"


def _check(site: str, url: str, timeout: int = 10) -> tuple[str, str, str]:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as r:
            code = r.getcode()
            final = r.geturl()
            if code == 404:
                return site, "no existe", url
            body = r.read(6000).decode(errors="replace").lower()
            if any(m in body for m in NOT_FOUND):
                return site, "no existe", url
            if r.geturl() != url and ("login" in final.lower() or "signin" in final.lower()):
                return site, "bloqueado-login", url
            return site, "posible perfil", final
    except Exception as e:
        msg = str(e)
        if "404" in msg or "Not Found" in msg:
            return site, "no existe", url
        if "429" in msg or "Too Many" in msg:
            return site, "limitado (429)", url
        if "403" in msg or "Forbidden" in msg:
            return site, "bloqueado (403)", url
        return site, f"error: {msg[:80]}", url


def search(username: str, timeout: int = 10, workers: int = 6) -> list[dict]:
    u = validate_username(username)
    jobs = [(name, tpl.format(u=u), level) for name, tpl, level in SITES]
    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        fut = {}
        for name, url, level in jobs:
            if name.lower() == "npm":
                fut[ex.submit(_check_npm, u, timeout)] = (name, f"https://www.npmjs.com/~{u}", level)
            else:
                fut[ex.submit(_check, name, url, timeout)] = (name, url, level)
        for f in concurrent.futures.as_completed(fut):
            name, url, level = fut[f]
            site, estado, final = f.result()
            if estado == "posible perfil" and level == "indicio":
                estado = "posible perfil (indicio, verificar a mano)"
            results.append({"sitio": site, "estado": estado, "url": final})
            time.sleep(0.05)
    order = {"posible perfil": 0, "posible perfil (indicio, verificar a mano)": 1}
    results.sort(key=lambda r: (order.get(r["estado"], 2), r["sitio"]))
    return results


def save_report(username: str, results: list[dict]) -> str:
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reportes")
    os.makedirs(base, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", username) or "usuario"
    path = os.path.join(base, f"reporte_user_{safe}_{ts}.txt")
    hits = [r for r in results if r["estado"].startswith("posible perfil")]
    with open(path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n DARKLY TOOLS - BUSQUEDA DE USUARIO (pasiva, educativa)\n" + "=" * 60 + "\n")
        f.write(f"Fecha: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\nUsuario: {username}\n")
        f.write(f"Posibles perfiles: {len(hits)}/{len(results)}\n\n")
        for r in results:
            f.write(f"[{r['estado']}] {r['sitio']}: {r['url']}\n")
        f.write("\nNota: 'indicio' = sitio con login/JS, verifica a mano en el navegador.\n")
    return path
