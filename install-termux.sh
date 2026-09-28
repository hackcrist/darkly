#!/data/data/com.termux/files/usr/bin/bash
# Darkly Tools - Instalador para Termux (Android)
# Uso: bash install-termux.sh
set -e

CYAN='\033[38;2;0;255;234m'; GREEN='\033[38;2;57;255;20m'
YELLOW='\033[38;2;255;255;0m'; RED='\033[38;2;255;49;49m'
BOLD='\033[1m'; END='\033[0m'

echo -e "${CYAN}${BOLD}  ____             _    _ ${END}"
echo -e "${GREEN}${BOLD} |  _ \  __ _ _ __| | _| |_   _${END}"
echo -e "${YELLOW}${BOLD} |____/ \__,_|_|  |_|\_\\\\_|\__, |${END}"
echo -e "${CYAN} Instalando Darkly Tools en Termux...${END}\n"

echo -e "${YELLOW}[1/4] Actualizando paquetes...${END}"
pkg update -y

echo -e "${YELLOW}[2/4] Instalando dependencias del sistema...${END}"
pkg install -y python go git iputils traceroute procps clang

echo -e "${YELLOW}[3/4] Instalando dependencias Python...${END}"
pip install --upgrade pip
if ! pip install -r requirements-termux.txt; then
  echo -e "${RED}psutil no compiló; instalando solo certifi (el sistema funciona igual).${END}"
  pip install certifi
fi

echo -e "${YELLOW}[4/4] Compilando darkly-go...${END}"
cd go
if go build -o darkly-go .; then
  echo -e "${GREEN}darkly-go compilado OK.${END}"
else
  echo -e "${RED}Go no compiló; el menú Python funciona igual como respaldo.${END}"
fi
cd ..

echo -e "\n${GREEN}${BOLD}Listo. Ejecuta: python darkly.py${END}"
echo -e "${CYAN}Nota: traceroute puede pedir root en algunos modos; ping y todo lo demás va sin root.${END}"
