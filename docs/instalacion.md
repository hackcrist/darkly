# Instalación

## Requisitos

- Python 3.10 o superior.
- Go 1.21 o superior (opcional).
- Conexión a internet para fuentes OSINT.

## Windows y Linux

```bash
git clone https://github.com/hackcrist/darkly.git
cd darkly
pip install -r requirements.txt
```

Verifica:

```bash
python darkly.py --version
```

## Go (opcional)

```bash
cd go
go build -o darkly-go.exe .   # en Linux: go build -o darkly-go .
```

Sin Go instalado el programa funciona igual con el código Python.

## Termux (Android)

Instala Termux desde F-Droid o GitHub (no Play Store):

```bash
pkg install git python -y
git clone https://github.com/hackcrist/darkly.git
cd darkly
python install.py
```

El instalador detecta el sistema, instala dependencias y compila `darkly-go` solo.

## Dependencias Python

- `psutil`: CPU, RAM, uptime y procesos (opcional, el programa avisa si falta).
- `certifi`: certificados SSL para HTTPS (requerido).
- `flask`, `gunicorn`: solo para la API web (`requirements-web.txt`).
