# Instalación

Requisitos: Python 3.10 o superior. Go 1.21 o superior solo para los módulos rápidos. Conexión a internet para las fuentes OSINT.

---

## Especificación Técnica

### Windows y Linux

```bash
git clone https://github.com/hackcrist/darkly.git
cd darkly
pip install -r requirements.txt
python darkly.py --version
```

### Dependencias Python

| Paquete | Uso | Obligatorio |
| :--- | :--- | :--- |
| `certifi` | Certificados SSL en todas las funciones HTTPS | Sí |
| `psutil` | CPU, RAM, uptime y procesos | No (el programa avisa y usa respaldo) |
| `flask`, `gunicorn` | API web (`requirements-web.txt`) | Solo para `webapp.py` |

### Compilación de Go

```bash
cd go
go build -o darkly-go.exe .   # en Linux: go build -o darkly-go .
```

Sin el binario compilado, el menú Python utiliza su propio código automáticamente.

### Termux (Android)

```bash
pkg install git python -y
git clone https://github.com/hackcrist/darkly.git
cd darkly
python install.py
```

El instalador detecta el sistema, instala dependencias del sistema y de pip, aplica permisos y compila `darkly-go`.

---

## Consideraciones Críticas y Casos de Borde

1. **PATH de Go en Windows:** tras instalar Go se debe abrir una terminal nueva para que el PATH se actualice.
2. **psutil en Termux:** si no compila, el instalador continúa solo con `certifi`; el sistema pierde CPU en vivo pero sigue operativo.
3. **Permisos en Termux:** `install.py` aplica `chmod +x` a los ejecutables; no se requiere almacenamiento externo porque los reportes viven dentro del proyecto.

---

## Ejemplo de Uso

```bash
pip install -r requirements.txt
python darkly.py
```
