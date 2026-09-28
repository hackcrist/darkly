#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Darkly Tools - API + web pública.

Segura por defecto:
  - Solo lectura/OSINT pasivo, con límite de peticiones por IP.
  - El escaneo de puertos viene DESACTIVADO (ENABLE_SCAN=1 + token para activarlo).
  - La verificación de contraseñas solo por POST (nunca en la URL/logs).
"""
import os
import threading
import time
from functools import wraps

from flask import Flask, jsonify, request, send_from_directory

from tools import networking, security, gathering, username

app = Flask(__name__, static_folder="web", static_url_path="")

TOKEN = os.environ.get("DARKLY_TOKEN", "")
ENABLE_SCAN = os.environ.get("ENABLE_SCAN", "0") == "1"

# Límite simple en memoria: {ip: [timestamps]}
_hits: dict[str, list[float]] = {}
_lock = threading.Lock()


def limited(per_min=30):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr or "?").split(",")[0].strip()
            now = time.time()
            with _lock:
                ts = [t for t in _hits.get(ip, []) if now - t < 60]
                if len(ts) >= per_min:
                    return jsonify({"error": "Límite excedido (demasiadas peticiones). Espera un minuto."}), 429
                ts.append(now)
                _hits[ip] = ts
            return fn(*a, **kw)
        return wrapper
    return deco


def need_token(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if TOKEN and request.headers.get("X-Token", "") != TOKEN:
            return jsonify({"error": "Requiere token (cabecera X-Token)."}), 401
        return fn(*a, **kw)
    return wrapper


@app.get("/")
def index():
    return send_from_directory("web", "index.html")


@app.get("/api/dns")
@limited(60)
def api_dns():
    host = request.args.get("host", "").strip()
    if not host:
        return jsonify({"error": "Falta ?host="}), 400
    try:
        return jsonify(networking.dns_lookup(networking.validate_target(host)))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/geo")
@limited(60)
def api_geo():
    ip = request.args.get("ip", "").strip()
    if not ip:
        return jsonify({"error": "Falta ?ip="}), 400
    return jsonify(gathering.ip_lookup(ip))


@app.get("/api/ptr")
@limited(60)
def api_ptr():
    ip = request.args.get("ip", "").strip()
    if not ip:
        return jsonify({"error": "Falta ?ip="}), 400
    return jsonify({"ip": ip, "ptr": gathering.reverse_dns(ip)})


@app.get("/api/rdap")
@limited(30)
def api_rdap():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Falta ?q="}), 400
    try:
        return jsonify(gathering.rdap_lookup(q))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/headers")
@limited(30)
def api_headers():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "Falta ?url="}), 400
    try:
        return jsonify(gathering.http_headers(url))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/urlscan")
@limited(60)
def api_urlscan():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "Falta ?url="}), 400
    try:
        return jsonify(security.scan_url(url))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/hash")
@limited(60)
def api_hash():
    text = request.args.get("text", "")
    algo = request.args.get("algo", "sha256")
    if not text:
        return jsonify({"error": "Falta ?text="}), 400
    try:
        return jsonify({"algo": algo, "hex": security.hash_text(text, algo)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/subdomains")
@limited(10)
def api_subdomains():
    domain = request.args.get("domain", "").strip()
    if not domain:
        return jsonify({"error": "Falta ?domain="}), 400
    try:
        return jsonify(gathering.subdomains_crtsh(domain))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/ghuser")
@limited(30)
def api_ghuser():
    u = request.args.get("u", "").strip()
    if not u:
        return jsonify({"error": "Falta ?u="}), 400
    try:
        return jsonify(gathering.github_profile(u))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/user")
@limited(5)
def api_user():
    u = request.args.get("u", "").strip()
    if not u:
        return jsonify({"error": "Falta ?u="}), 400
    try:
        u = username.validate_username(u)
        return jsonify({"usuario": u, "resultados": username.search(u)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/breach")
@limited(10)
def api_breach():
    data = request.get_json(silent=True) or {}
    pw = data.get("password", "")
    if not pw:
        return jsonify({"error": "Manda JSON {\"password\": \"...\"}"}), 400
    r = security.check_password_breach(pw)
    del pw
    return jsonify(r)


@app.get("/api/scan")
@limited(5)
@need_token
def api_scan():
    if not ENABLE_SCAN:
        return jsonify({"error": "Escaneo desactivado en este servidor (ENABLE_SCAN=0)."}), 403
    host = request.args.get("host", "").strip()
    ports = request.args.get("ports", "22,80,443")
    if not host:
        return jsonify({"error": "Falta ?host="}), 400
    try:
        host = networking.validate_target(host)
        plist = networking.parse_ports(ports)[:50]
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    res = networking.port_scan(host, plist)
    out = {}
    for p, is_open in res.items():
        if p == "error":
            continue
        out[str(p)] = {"open": bool(is_open),
                       "banner": networking.banner_grab(host, p) if is_open else ""}
    return jsonify({"host": host, "ports": out})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
