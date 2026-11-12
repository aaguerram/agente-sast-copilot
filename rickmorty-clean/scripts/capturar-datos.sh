#!/usr/bin/env bash
# Captura TODA la información de la API GraphQL de Rick and Morty y guarda las respuestas
# tal cual (sin transformar) en src/RickMorty.Infrastructure/Data/*.json.
# La API REST lee esos archivos; ya no llama a GraphQL en tiempo de ejecución.
# Volver a ejecutar solo para refrescar la data quemada:  ./scripts/capturar-datos.sh
set -euo pipefail

ENDPOINT="${GRAPHQL_ENDPOINT:-https://rickandmortyapi.com/graphql}"
DEST="$(cd "$(dirname "$0")/.." && pwd)/src/RickMorty.Infrastructure/Data"
mkdir -p "$DEST"

gql() { # $1 = query GraphQL
  python3 -c 'import json,sys; print(json.dumps({"query": sys.argv[1]}))' "$1" |
    curl -fsS "$ENDPOINT" -H 'Content-Type: application/json' -A 'RickMorty-Clean-Api' --data-binary @-
}

total() { # $1 = characters | episodes | locations
  gql "{ $1 { info { count } } }" |
    python3 -c "import json,sys; print(json.load(sys.stdin)['data']['$1']['info']['count'])"
}

ids() { seq -s, 1 "$1"; }

capturar() { # $1 = archivo, $2 = query
  gql "$2" > "$DEST/$1.tmp"
  python3 -c '
import json, sys
doc = json.load(open(sys.argv[1]))
if doc.get("errors"):
    sys.exit("GraphQL devolvió errores: %s" % doc["errors"][0].get("message"))
' "$DEST/$1.tmp"
  mv "$DEST/$1.tmp" "$DEST/$1"
  echo ">> $1 ($(wc -c < "$DEST/$1") bytes)"
}

capturar characters.json "{ charactersByIds(ids: [$(ids "$(total characters)")]) {
  id name status species type gender image
  origin { id name } location { id name } episode { id } } }"

capturar episodes.json "{ episodesByIds(ids: [$(ids "$(total episodes)")]) {
  id name air_date episode characters { id } } }"

capturar locations.json "{ locationsByIds(ids: [$(ids "$(total locations)")]) {
  id name type dimension residents { id } } }"
