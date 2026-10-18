#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Darkly Tools | Herramientas de Linux y seguridad
Solo fines educativos. Uso responsable y autorizado.
"""
import os
import sys
import time
import contextlib

__version__ = "2.0.0"

# Fuerza UTF-8 en consola Windows para evitar errores con tildes/cajas
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from tools import networking, security, gathering, system_tools, reporter, username, gospeed

# Activa colores ANSI en Windows 10+
if os.name == "nt":
    try:
        os.system("")
    except Exception:
        pass

class C:
    R = "\033[91m"; G = "\033[92m"; Y = "\033[93m"
    B = "\033[94m"; M = "\033[95m"; C = "\033[96m"
    W = "\033[97m"; D = "\033[90m"; BOLD = "\033[1m"
    DIM = "\033[2m"; END = "\033[0m"

    # --- Neon truecolor ---
    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        return f"\033[38;2;{r};{g};{b}m"

    NC = "\033[38;2;0;255;234m"      # neon cyan
    NP = "\033[38;2;255;0;255m"      # neon magenta
    NG = "\033[38;2;57;255;20m"      # neon green
    NY = "\033[38;2;255;255;0m"      # neon yellow
    NB = "\033[38;2;0;150;255m"      # neon blue
    NO = "\033[38;2;255;110;0m"      # neon orange
    NV = "\033[38;2;176;38;255m"     # neon violet


def neon_text(text: str, c1: tuple[int, int, int], c2: tuple[int, int, int]) -> str:
    """Degradado neon letra por letra entre dos colores RGB."""
    if not text:
        return text
    out = []
    n = max(len(text) - 1, 1)
    for i, ch in enumerate(text):
        r = int(c1[0] + (c2[0] - c1[0]) * i / n)
        g = int(c1[1] + (c2[1] - c1[1]) * i / n)
        b = int(c1[2] + (c2[2] - c1[2]) * i / n)
        out.append(f"\033[38;2;{r};{g};{b}m{C.BOLD}{ch}")
    return "".join(out) + C.END


_BANNER_RAW = [
    r"  ____             _    _",
    r" |  _ \  __ _ _ __| | _| |_   _",
    r" | | | |/ _` | '__| |/ / | | | |",
    r" | |_| | (_| | |  |   <| | |_| |",
    r" |____/ \__,_|_|  |_|\_\\_|\__, |",
    r"                          |___/",
]
_BANNER_COLORS = [C.NC, C.NC, C.NG, C.NY, C.NP, C.NV]


def build_banner() -> str:
    lines = []
    for raw, col in zip(_BANNER_RAW, _BANNER_COLORS):
        lines.append(f"{col}{C.BOLD}{raw}{C.END}")
    # sombra neon inferior
    lines.append(f"{C.DIM}{C.NV}{'-' * 52}{C.END}")
    sub = neon_text("Herramientas de Linux y Seguridad", (0, 255, 234), (255, 0, 255))
    etiqueta = neon_text("(educativo)", (255, 255, 0), (255, 110, 0))
    lines.append(f"  {sub} {etiqueta}")
    return "\n".join(lines)


BANNER = build_banner()

LINE = f"{C.D}{'-' * 52}{C.END}"


def clear():
    # No limpiar cuando la salida va a un pipe (tests)
    if not sys.stdout.isatty():
        return
    os.system("cls" if os.name == "nt" else "clear")


def show_banner():
    print()
    print(BANNER)
    ver = neon_text(f"v{__version__}", (255, 255, 0), (255, 110, 0))
    print(f" {ver}")
    aviso = neon_text("Solo fines educativos. Usalo con responsabilidad y autorizacion.", (255, 255, 0), (0, 255, 234))
    print(f" {aviso}\n")


def title(t: str):
    bar = f"{C.NC}+--{C.END} {neon_text(t, (0, 255, 234), (255, 255, 0))} {C.NC}{'-' * max(38 - len(t), 4)}+{C.END}"
    print(f"\n{C.BOLD}{bar}{C.END}")


def menu(options: list[tuple[str, str]]):
    print(f" {C.DIM}{C.NV}|{C.END}")
    for key, label in options:
        if key == "0":
            box = f"{C.NO}{C.BOLD}[{key}]{C.END}"
            arrow = f"{C.D}<{C.END}"
            lab = f"{C.D}{label}{C.END}"
        else:
            # numero neon alternado cyan/verde/magenta
            ncol = [C.NC, C.NG, C.NP, C.NY, C.NB, C.NV][int(key) % 6] if key.isdigit() else C.NC
            box = f"{ncol}{C.BOLD}[{key}]{C.END}"
            arrow = f"{ncol}>{C.END}"
            lab = f"{C.W}{C.BOLD}{label}{C.END}"
        print(f" {C.DIM}{C.NV}|{C.END}  {box} {arrow} {lab}")
    print(f" {C.DIM}{C.NV}+{'-' * 50}+{C.END}")


def ask(prompt: str) -> str:
    try:
        return input(f" {C.NC}{C.BOLD}>{C.END} {C.W}{prompt}:{C.END} ").strip()
    except EOFError:
        # Sin entrada (p. ej. un pipe o CI): salir limpio en vez de reventar.
        print()
        raise SystemExit(0)


def ask_int(prompt: str, default: int | None = None, minimo: int | None = None, maximo: int | None = None) -> int:
    """Pide un numero entero validado; evita que un texto suelto rompa el menu."""
    raw = ask(prompt)
    if raw == "" and default is not None:
        return default
    try:
        valor = int(raw)
    except ValueError:
        raise ValueError(f"Se esperaba un numero entero y recibi '{raw}'.")
    if minimo is not None and valor < minimo:
        raise ValueError(f"Valor fuera de rango (minimo {minimo}).")
    if maximo is not None and valor > maximo:
        raise ValueError(f"Valor fuera de rango (maximo {maximo}).")
    return valor


def ok(msg: str):
    print(f" {C.NG}{C.BOLD}[OK]{C.END} {C.W}{msg}{C.END}")


def err(msg: str):
    print(f" {C.rgb(255,49,49)}{C.BOLD}[!]{C.END} {msg}")


def warn(msg: str):
    print(f" {C.NY}{C.BOLD}[*]{C.END} {msg}")


def print_kv(data, indent: str = "   "):
    if isinstance(data, dict):
        w = max((len(str(k)) for k in data), default=0)
        for k, v in data.items():
            if k == "error" or (isinstance(v, str) and v.startswith("[!]")):
                col = C.rgb(255, 49, 49)
            elif isinstance(v, str) and v == "MISSING":
                col = C.rgb(255, 49, 49)
            elif v is None or (isinstance(v, str) and v in ("", "?", "-")):
                col = C.D
            elif isinstance(v, (int, float)):
                col = C.NY
            else:
                col = C.W
            print(f"{indent}{C.NC}{str(k):<{w}}{C.END} {C.DIM}:{C.END} {col}{v}{C.END}")
    elif isinstance(data, (list, tuple)):
        for item in data:
            if isinstance(item, dict):
                print_kv(item, indent + "  ")
                print(f"{indent}{C.DIM}{'-' * 30}{C.END}")
            else:
                print(f"{indent}{C.NG}-{C.END} {C.W}{item}{C.END}")
    else:
        print(f"{indent}{data}")


@contextlib.contextmanager
def timed(label: str):
    """Mide y muestra el tiempo real de una operacion."""
    t0 = time.perf_counter()
    yield
    print(f" {C.DIM}[{label}: {time.perf_counter() - t0:.2f}s]{C.END}")


def show_ports(titulo: str, items: dict):
    """Tabla de puertos estilo nmap: PORT / STATE / SERVICE / DETALLE.
    items: {puerto: (abierto: bool, detalle: str)}"""
    print(f"\n {C.BOLD}{'PORT':<8} {'STATE':<8} {'SERVICE':<16} DETALLE{C.END}")
    print(LINE)
    n_open = 0
    for p in sorted(items, key=lambda x: int(x) if str(x).isdigit() else 0):
        abierto, detalle = items[p]
        n_open += int(bool(abierto))
        estado = f"{C.NG}open{C.END}" if abierto else f"{C.D}closed{C.END}"
        serv = networking.service_for(int(p), "" if not abierto else str(detalle))
        col = C.W if abierto else C.D
        print(f" {str(p):<8} {estado:<16} {serv:<16} {col}{detalle or '-'}{C.END}")
    print(LINE)
    print(f" {C.DIM}{titulo}: {n_open} abiertos / {len(items)} probados{C.END}")


def pause():
    try:
        input(f"\n {C.DIM}Pulsa Enter para continuar...{C.END}")
    except EOFError:
        print()
        raise SystemExit(0)


def confirm_auth() -> bool:
    print(f"\n {C.NO}{C.BOLD}Zona sensible:{C.END} {C.W}solo equipos propios o con autorizacion escrita.{C.END}")
    ans = ask("Confirmas que tienes autorizacion? [s/N]").lower()
    return ans in ("s", "si", "sí", "y", "yes")


def networking_menu():
    while True:
        clear(); show_banner(); title("REDES")
        menu([("1", "Consultar DNS (con respaldo DoH)"), ("2", "Ping"), ("3", "Escaneo de puertos (autorizado)"),
              ("4", "Traceroute"), ("5", "Calculadora de subred"), ("6", "Banner grab (preciso)"),
              ("7", "DNS rápido Go"), ("8", "Escaneo rápido Go (autorizado)"), ("0", "Volver")])
        c = ask("Elige")
        if c == "0":
            return
        try:
            if c == "1":
                host_d = networking.validate_target(ask("Host"))
                with timed("DNS"):
                    res_d = networking.dns_lookup(host_d)
                print_kv(res_d)
            elif c == "2":
                host_p = networking.validate_target(ask("Host"))
                with timed("ping"):
                    salida_p = networking.ping_host(host_p)
                print(f"\n{salida_p}")
            elif c == "3":
                if not confirm_auth():
                    err("Escaneo cancelado - se requiere autorización."); pause(); continue
                host = networking.validate_target(ask("Host/IP"))
                ports = networking.parse_ports(ask("Puertos (ej. 22,80,443 o 1-1024)"))
                warn(f"Escaneando {host} ({len(ports)} puertos)...")
                with timed("escaneo"):
                    res = networking.port_scan(host, ports)
                if "error" in res:
                    err(str(res["error"])); pause(); continue
                items = {}
                for p in sorted(res):
                    items[p] = (True, networking.banner_grab(host, p)) if res[p] else (False, "cerrado")
                show_ports(f"Escaneo de {host}", items)
            elif c == "4":
                warn("Trazando ruta (puede tardar)...")
                host_t = networking.validate_target(ask("Host/IP"))
                with timed("traceroute"):
                    salida_t = networking.traceroute(host_t)
                print(f"\n{salida_t}")
            elif c == "5":
                print_kv(networking.subnet_info(ask("CIDR (ej. 192.168.1.0/24)")))
            elif c == "6":
                host = networking.validate_target(ask("Host/IP"))
                port = ask_int("Puerto (ej. 22)", minimo=1, maximo=65535)
                ok(networking.banner_grab(host, port))
            elif c == "7":
                host = networking.validate_target(ask("Host"))
                try:
                    with timed("DNS Go"):
                        res_go = gospeed.go_dns_lookup(host)
                    print_kv(res_go)
                except RuntimeError as e:
                    warn(f"{e} Usando Python...")
                    print_kv(networking.dns_lookup(host))
            elif c == "8":
                if not confirm_auth():
                    err("Escaneo cancelado - se requiere autorización."); pause(); continue
                host = networking.validate_target(ask("Host/IP"))
                prange = ask("Puertos (ej. 22,80,443 o 1-1024)")
                try:
                    warn("Escaneando con Go (goroutines)...")
                    with timed("escaneo Go"):
                        data = gospeed.go_port_scan(host, prange)
                    print(f"   IP: {data.get('ip', '?')}")
                    items = {}
                    for p, info in data.get("ports", {}).items():
                        items[p] = (bool(info.get("open")), info.get("banner", "") or "cerrado")
                    show_ports(f"Escaneo Go de {host}", items)
                except RuntimeError as e:
                    warn(f"{e} Usando Python...")
                    ports = networking.parse_ports(prange)
                    with timed("escaneo"):
                        res = networking.port_scan(host, ports)
                    if "error" in res:
                        err(str(res["error"]))
                    else:
                        items = {p: ((True, networking.banner_grab(host, p)) if res[p] else (False, "cerrado")) for p in res}
                        show_ports(f"Escaneo de {host}", items)
            else:
                err("Opción no válida")
        except Exception as e:
            err(str(e))
        pause()


def security_menu():
    while True:
        clear(); show_banner(); title("SEGURIDAD DEFENSIVA")
        menu([("1", "Generar hash"), ("2", "Identificar hash"), ("3", "Fortaleza de contraseña"),
              ("4", "Generar contraseña"), ("5", "Cabeceras de seguridad"), ("6", "Analizar URL"),
              ("7", "Auditoría completa (fortaleza+filtración)"), ("0", "Volver")])
        c = ask("Elige")
        try:
            if c == "0":
                return
            if c == "1":
                t = ask("Texto")
                a = ask("Algoritmo [sha256]") or "sha256"
                ok(security.hash_text(t, a))
            elif c == "2":
                print_kv({"posibles": ", ".join(security.identify_hash(ask("Hash")))})
            elif c == "3":
                import getpass
                pw = getpass.getpass(f" {C.Y}> Contraseña:{C.END} ")
                r = security.password_strength(pw)
                print_kv(r)
            elif c == "4":
                nueva = security.generate_password(ask_int("Longitud [16]", default=16, minimo=8, maximo=64))
                ok(f"Generada: {nueva}")
                warn("Verificando que lo generado no esté filtrado...")
                b = security.check_password_breach(nueva)
                if b.get("error"):
                    warn(f"No se pudo verificar contra filtraciones: {b['error']}")
                elif b.get("comprometida"):
                    err(f"Ojo: lo generado aparece {b['veces_vista']} veces. Genera otra.")
                else:
                    ok("Lo generado no aparece en filtraciones.")
            elif c == "5":
                print_kv(security.check_security_headers(ask("URL")))
            elif c == "6":
                r = security.scan_url(ask("URL"))
                col = C.NG if r["nivel"] == "Bajo" else C.NY if r["nivel"] == "Medio" else C.rgb(255, 49, 49)
                print(f"\n   Riesgo: {col}{C.BOLD}{r['riesgo']}/100 ({r['nivel']}){C.END}")
                print_kv({"hallazgos": r["hallazgos"]})
            elif c == "7":
                import getpass
                pw = getpass.getpass(f" {C.NC}{C.BOLD}>{C.END} Contraseña a auditar (no se muestra): ")
                warn("Auditando fortaleza + filtración en una pasada...")
                a = security.audit_password(pw)
                del pw
                print(f"\n {C.NC}{C.BOLD}-- Fortaleza --{C.END}"); print_kv(a["fortaleza"])
                print(f"\n {C.NP}{C.BOLD}-- Filtración --{C.END}"); print_kv(a["filtracion"])
                print(f"\n {C.NY}{C.BOLD}Veredicto:{C.END} {a['veredicto']}")
            else:
                err("Opción no válida")
        except Exception as e:
            err(str(e))
        pause()


def gathering_menu():
    while True:
        clear(); show_banner(); title("RECOLECCION PASIVA")
        menu([("1", "Mi IP pública (multi-fuente)"), ("2", "Consultar IP (validada)"), ("3", "Cabeceras HTTP (HEAD+GET)"),
              ("4", "DNS inverso"), ("5", "WHOIS (puerto 43)"), ("6", "RDAP (HTTPS, no falla)"),
              ("7", "Buscar nombre de usuario (pasivo)"), ("8", "Registros DNS (A/MX/TXT/NS)"),
              ("9", "Subdominios (crt.sh)"), ("10", "Perfil GitHub"), ("0", "Volver")])
        c = ask("Elige")
        try:
            if c == "0":
                return
            if c == "1":
                with timed("mi IP"):
                    info = gathering.public_ip_info()
                print_kv(info)
                ip = info.get("query", "") if isinstance(info, dict) else ""
                if ip and "error" not in info:
                    auto_save_ip(ip, objetivo=f"mi-ip ({ip})")
            elif c == "2":
                entrada = ask("IP o dominio")
                try:
                    ip, objetivo = resolve_ip_input(entrada)
                except ValueError:
                    ip, objetivo = entrada.strip(), entrada.strip()
                print_kv(gathering.ip_lookup(ip))
                try:
                    auto_save_ip(ip, nombre=(objetivo if objetivo != ip else None), objetivo=objetivo)
                except Exception as e:
                    err(f"Auto-guardado falló: {e}")
            elif c == "3":
                print_kv(gathering.http_headers(ask("URL")))
            elif c == "4":
                entrada = ask("IP o dominio")
                try:
                    ip, objetivo = resolve_ip_input(entrada)
                except ValueError:
                    ip, objetivo = entrada.strip(), entrada.strip()
                ok(gathering.reverse_dns(ip))
                try:
                    auto_save_ip(ip, nombre=(objetivo if objetivo != ip else None), objetivo=objetivo)
                except Exception as e:
                    err(f"Auto-guardado falló: {e}")
            elif c == "5":
                print(f"\n{gathering.whois_lookup(ask('Dominio/IP'))}")
            elif c == "6":
                q6 = ask("Dominio/IP (ej. google.com u 8.8.8.8)")
                with timed("RDAP"):
                    r6 = gathering.rdap_lookup(q6)
                print_kv(r6)
            elif c == "7":
                u = username.validate_username(ask("Nombre de usuario (sin @)"))
                warn(f"Buscando '{u}' en {len(username.SITES)} sitios públicos (puede tardar ~30s)...")
                with timed("busqueda"):
                    res = username.search(u)
                hits = [r for r in res if r["estado"].startswith("posible perfil")]
                print(f"\n {C.NG}{C.BOLD}Posibles perfiles: {len(hits)}/{len(res)}{C.END}")
                for r in res:
                    if r["estado"].startswith("posible perfil"):
                        print(f"   {C.NG}[+] {r['sitio']}: {r['url']}  ({r['estado']}){C.END}")
                    elif r["estado"] in ("no existe",):
                        print(f"   {C.D}[-] {r['sitio']}: no existe{C.END}")
                    else:
                        print(f"   {C.Y}[?] {r['sitio']}: {r['estado']}{C.END}")
                path = username.save_report(u, res)
                print(f"\n {C.NY}Guardado: {path}{C.END}")
            elif c == "8":
                print_kv(gathering.dns_records(ask("Dominio (ej. google.com)")))
            elif c == "9":
                d9 = ask("Dominio (ej. google.com)")
                with timed("crt.sh"):
                    r = gathering.subdomains_crtsh(d9)
                print_kv({k: v for k, v in r.items() if k != "subdominios"})
                for s in r.get("subdominios", [])[:50]:
                    print(f"   - {s}")
            elif c == "10":
                u10 = ask("Usuario GitHub (sin @)")
                with timed("GitHub"):
                    r10 = gathering.github_profile(u10)
                print_kv(r10)
            else:
                err("Opción no válida")
        except Exception as e:
            err(str(e))
        pause()


def system_menu():
    while True:
        clear(); show_banner(); title("SISTEMA")
        menu([("1", "Info + disco"), ("2", "Tiempo encendido"), ("3", "Procesos"),
              ("4", "Hash de archivo"), ("5", "Verificar hash (preciso)"), ("6", "Revisar permisos"), ("7", "Ver final del log"), ("0", "Volver")])
        c = ask("Elige")
        try:
            if c == "0":
                return
            if c == "1":
                print(f"\n {C.NC}{C.BOLD}-- Sistema --{C.END}"); print_kv(system_tools.sys_info())
                print(f"\n {C.NG}{C.BOLD}-- Disco --{C.END}"); print_kv(system_tools.disk_usage())
                print(f"\n {C.NP}{C.BOLD}-- CPU/RAM --{C.END}"); print_kv(system_tools.try_psutil_stats())
            elif c == "2":
                ok(system_tools.get_uptime())
            elif c == "3":
                for p in system_tools.list_processes():
                    print_kv(p)
            elif c == "4":
                print_kv(system_tools.file_hash(ask("Ruta del archivo"), ask("Algoritmo [sha256]") or "sha256"))
            elif c == "5":
                r = system_tools.file_hash_verify(ask("Ruta del archivo"), ask("Hash esperado"), ask("Algoritmo [sha256]") or "sha256")
                (ok if r["coincide"] else err)(r["resultado"])
                print_kv(r)
            elif c == "6":
                print_kv(system_tools.check_permissions(ask("Ruta")))
            elif c == "7":
                for line in system_tools.tail_log(ask("Ruta del log"), ask_int("Líneas [20]", default=20, minimo=1, maximo=200)):
                    print(f"   {line}")
            else:
                err("Opción no válida")
        except Exception as e:
            err(str(e))
        pause()


def resolve_ip_input(s: str) -> tuple[str, str]:
    """Acepta IP o dominio. Devuelve (ip, objetivo_original). Vale con nombre específico."""
    s = s.strip()
    if not s:
        raise ValueError("Entrada vacía. Vale IP (8.8.8.8) o dominio (google.com).")
    orig = s
    if "://" in s or "/" in s:
        s = networking.validate_target(s)
    import ipaddress as _ip
    try:
        _ip.ip_address(s)
        return s, orig
    except ValueError:
        pass
    # Es dominio/nombre: resuelve
    ip = networking.resolve_host(s)
    if ip.startswith("[!]"):
        raise ValueError(f"No se pudo resolver '{s}': {ip}")
    return ip, orig


def auto_save_ip(ip: str, nombre: str | None = None, objetivo: str = "") -> tuple[str, str] | tuple[None, None]:
    """Recolecta geo+PTR+RDAP y guarda HTML/TXT automáticamente. Vale nombre específico."""
    try:
        try:
            geo = gathering.ip_lookup(ip)
        except Exception as e:
            geo = {"error": str(e)}
        try:
            ptr = gathering.reverse_dns(ip)
        except Exception as e:
            ptr = f"[!] {e}"
        try:
            rdap = gathering.rdap_lookup(ip)
        except Exception as e:
            rdap = {"error": str(e)}
        g = geo if isinstance(geo, dict) else {"dato": str(geo)}
        r = rdap if isinstance(rdap, dict) else {"dato": str(rdap)}
        h, t, c, p, j = reporter.build_ip_report(ip, g, str(ptr), r, nombre=nombre, objetivo=objetivo or ip)
        print(f"\n {C.NG}{C.BOLD}Auto-guardado en reportes/:{C.END}")
        print(f"   HTML: {h}\n   TXT : {t}\n   CSV : {c}\n   PDF : {p}\n   JSON: {j}")
        return h, t
    except Exception as e:
        err(f"No se pudo auto-guardar: {e}")
        return None, None


def ip_menu():
    while True:
        clear(); show_banner(); title("INFO POR IP (auto-guarda HTML/TXT)")
        menu([("1", "Mi IP publica"), ("2", "Informacion por IP (geo/org/isp)"),
              ("3", "DNS inverso (PTR)"), ("4", "RDAP de IP (registro preciso)"),
              ("5", "Informe completo + guardar HTML/TXT"), ("6", "Ver reportes guardados"), ("0", "Volver")])
        c = ask("Elige")
        try:
            if c == "0":
                return
            if c == "1":
                with timed("mi IP"):
                    info = gathering.public_ip_info()
                print_kv(info)
                ip = info.get("query", "") if isinstance(info, dict) else ""
                if ip and "error" not in info:
                    nombre = ask("Nombre especifico para el reporte [Enter=auto]") or None
                    auto_save_ip(ip, nombre=nombre, objetivo=f"mi-ip ({ip})")
            elif c == "2":
                entrada = ask("IP o dominio (ej. 8.8.8.8 o google.com)")
                ip, objetivo = resolve_ip_input(entrada)
                if objetivo != ip:
                    ok(f"{objetivo} -> {ip}")
                print_kv(gathering.ip_lookup(ip))
                nombre = ask("Nombre especifico para el reporte [Enter=auto]") or (objetivo if objetivo != ip else None)
                auto_save_ip(ip, nombre=nombre, objetivo=objetivo)
            elif c == "3":
                entrada = ask("IP o dominio")
                ip, objetivo = resolve_ip_input(entrada)
                ok(gathering.reverse_dns(ip))
                nombre = ask("Nombre especifico para el reporte [Enter=auto]") or (objetivo if objetivo != ip else None)
                auto_save_ip(ip, nombre=nombre, objetivo=objetivo)
            elif c == "4":
                entrada = ask("IP o dominio (ej. 8.8.8.8 o google.com)")
                ip, objetivo = resolve_ip_input(entrada)
                print_kv(gathering.rdap_lookup(ip))
                nombre = ask("Nombre especifico para el reporte [Enter=auto]") or (objetivo if objetivo != ip else None)
                auto_save_ip(ip, nombre=nombre, objetivo=objetivo)
            elif c == "5":
                entrada = ask("IP o dominio (ej. 8.8.8.8 o google.com)")
                ip, objetivo = resolve_ip_input(entrada)
                nombre = ask("Nombre especifico para el reporte [Enter=auto]") or (objetivo if objetivo != ip else None)
                warn(f"Recolectando informe 10/10 de {ip} (geo+PTR+RDAP+ping+puertos+headers)...")
                with timed("geo multi-fuente"):
                    geo = gathering.ip_lookup_multi(ip)
                ptr = gathering.reverse_dns(ip)
                try:
                    rdap = gathering.rdap_lookup(ip)
                except Exception as e:
                    rdap = {"error": str(e)}
                try:
                    dns_d = networking.dns_lookup(objetivo)
                except Exception as e:
                    dns_d = {"error": str(e)}
                try:
                    ping_d = networking.ping_host(ip, count=2)
                except Exception as e:
                    ping_d = str(e)
                puertos_d: dict = {}
                for p in (22, 80, 443, 8080, 3389):
                    try:
                        if networking.check_port(ip, p, timeout=1.0):
                            puertos_d[p] = networking.banner_grab(ip, p)
                        else:
                            puertos_d[p] = "cerrado"
                    except Exception as e:
                        puertos_d[p] = f"error: {e}"
                try:
                    headers_d = gathering.http_headers(ip)
                except Exception as e:
                    headers_d = {"error": str(e)}
                print(f"\n {C.NC}{C.BOLD}-- Geo/Org --{C.END}")
                print_kv({k: v for k, v in geo.items() if k != "verificacion"} if isinstance(geo, dict) else geo)
                if isinstance(geo, dict) and geo.get("verificacion"):
                    vf = geo["verificacion"]
                    print(f"\n {C.NP}{C.BOLD}-- Verificacion multi-fuente --{C.END}")
                    print_kv({"fuentes_ok": vf.get("fuentes_ok"), "fuentes_error": vf.get("fuentes_error"),
                              "coincide_pais": vf.get("coincide_pais"), "coincide_asn": vf.get("coincide_asn")})
                    for aviso in (vf.get("avisos") or []):
                        warn(aviso)
                    for d in (vf.get("detalle") or []):
                        print(f"   {C.DIM}- {d.get('fuente')}: {d.get('pais')} / {d.get('org')} / {d.get('asn')}{C.END}")
                print(f"\n {C.NG}{C.BOLD}-- PTR --{C.END}"); ok(ptr)
                print(f"\n {C.NP}{C.BOLD}-- RDAP --{C.END}"); print_kv(rdap)
                print(f"\n {C.NY}{C.BOLD}-- Puertos --{C.END}"); print_kv(puertos_d)
                extra = {"dns": dns_d, "ping": ping_d, "puertos": puertos_d, "headers": headers_d,
                         "notas": f"Objetivo {objetivo}, informe completo 10/10"}
                h, t, c, p, j = reporter.build_ip_report(ip, geo if isinstance(geo, dict) else {"dato": geo}, str(ptr), rdap if isinstance(rdap, dict) else {"dato": rdap}, nombre=nombre, objetivo=objetivo, extra=extra)
                print(f"\n {C.NY}{C.BOLD}Guardado en carpeta reportes/:\n   HTML: {h}\n   TXT : {t}\n   CSV : {c}\n   PDF : {p}\n   JSON: {j}{C.END}")
                print(f" {C.D}Abre reportes/index.html en tu navegador para verlo super mejor.{C.END}")
            elif c == "6":
                reps = reporter.list_reports()
                if not reps:
                    warn("Aún no hay reportes. Usa la opción 5 primero.")
                else:
                    print(f"\n {C.BOLD}Carpeta: {reporter.ensure_dir()}{C.END}")
                    for r in reps[:20]:
                        print(f"   - {r}")
            else:
                err("Opción no válida")
        except Exception as e:
            err(str(e))
        pause()


def main():
    clear(); show_banner()
    while True:
        print(f" {C.NP}{C.BOLD}+-- MENU PRINCIPAL ------------------------------+{C.END}")
        menu([("1", "Redes"), ("2", "Seguridad"), ("3", "Recolección info"), ("4", "Sistema"), ("5", "IP / Info por IP"), ("0", "Salir")])
        c = ask("Elige")
        if c == "0":
            print(f"\n {neon_text('Adios. Hackea el aprendizaje, no sistemas.', (0, 255, 234), (255, 0, 255))}\n")
            sys.exit(0)
        elif c == "1":
            networking_menu()
        elif c == "2":
            security_menu()
        elif c == "3":
            gathering_menu()
        elif c == "4":
            system_menu()
        elif c == "5":
            ip_menu()
        else:
            err("Opción no válida"); pause()
        clear(); show_banner()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("-v", "--version", "version"):
        print(f"Darkly Tools v{__version__}")
        sys.exit(0)
    main()
