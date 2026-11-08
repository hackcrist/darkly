# Darkly Tools - API web (webapp.py)
FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema (ca-certificates para HTTPS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt

# Código de la aplicación (estructura de paquetes)
COPY darkly ./darkly
COPY web ./web

# Puerto de la API
EXPOSE 5000

# Token obligatorio: pasar con -e DARKLY_TOKEN=xxx al correr el contenedor
ENV DARKLY_TOKEN=""
ENV ENABLE_SCAN="0"
ENV RATE_LIMIT_ENABLED="1"
ENV TRUST_PROXY="0"

# Punto de entrada: ejecutar como módulo para que resuelva paquetes
ENTRYPOINT ["python", "-m", "darkly.api.webapp"]
