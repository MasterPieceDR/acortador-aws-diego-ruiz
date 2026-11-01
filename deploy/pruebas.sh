#!/usr/bin/env bash
# Pruebas del punto 10 del enunciado contra la API desplegada.
# Uso: bash deploy/pruebas.sh http://<ip-publica-ec2>:8000
set -u
API="${1:?Pasa la URL de la API, por ejemplo http://3.90.10.20:8000}"

echo "== 1. POST /shorten (crea UUID y guarda en DynamoDB)"
RESP=$(curl -s -X POST "$API/shorten" -H "Content-Type: application/json" \
  -d '{"original_url":"https://www.example.com/articulos/arquitectura-cloud"}')
echo "$RESP"
CODE=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['short_code'])")

echo; echo "== 2. GET /$CODE (redirección HTTP real)"
curl -s -o /dev/null -w "HTTP %{http_code} -> Location: %{redirect_url}\n" "$API/$CODE"

echo; echo "== 3. GET /urls/$CODE (información del enlace)"
curl -s "$API/urls/$CODE"; echo

echo; echo "== 4. UUID inexistente (debe ser 404)"
curl -s -w "  HTTP %{http_code}\n" "$API/00000000-0000-4000-8000-000000000000"

echo; echo "== 5. URL inválida (debe ser 422)"
curl -s -w "  HTTP %{http_code}\n" -X POST "$API/shorten" -H "Content-Type: application/json" \
  -d '{"original_url":"ftp://archivo"}'

echo; echo "Guarda este código para probar después de reiniciar: $CODE"
echo "Tras 'sudo systemctl restart shortener' (o reiniciar la instancia):"
echo "  curl -s -o /dev/null -w '%{http_code}\n' $API/$CODE   -> debe seguir dando 307"
