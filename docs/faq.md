# FAQ

## Error SSL o CERTIFICATE_VERIFY_FAILED

Instala certificados con `pip install -r requirements.txt` (incluye `certifi`). Si tu red tiene filtro TLS (escuela o trabajo), algunos endpoints se interceptan: el programa ya prefiere los que verifican limpio.

## WHOIS dice "puerto 43 bloqueado"

Normal en redes filtradas. Usa la opción RDAP, que va por HTTPS y entrega lo mismo.

## crt.sh falla o tarda

Su servidor es inestable (responde 502 a ratos). Hay 3 reintentos con respaldo HackerTarget automáticos.

## npm, Telegram o Medium salen "bloqueados"

Esas páginas bloquean bots. npm se consulta por su API oficial; el resto se marca como indicio y se verifica a mano en el navegador.

## Sin registro PTR

Significa que el dueño de la IP no creó reverso. Normal en móviles y nubes. No es error del programa.

## Go no se reconoce

Instálalo desde https://go.dev/dl/ y abre una terminal nueva (el PATH se actualiza al reabrir).
