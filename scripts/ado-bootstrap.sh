#!/usr/bin/env bash
# Sube este repositorio a un proyecto de Azure DevOps y deja el pipeline corriendo en
# cada pull request a main. Es idempotente: se puede ejecutar las veces que haga falta.
#
#   ./scripts/ado-bootstrap.sh --org https://dev.azure.com/MI_ORG --project MI_PROYECTO [--dry-run]
#
# Sin Azure CLI instalado, córrelo dentro del contenedor de az (docker compose):
#   ./scripts/ado.sh az login --use-device-code
#   ./scripts/ado.sh ./scripts/ado-bootstrap.sh --org ... --project ... --dry-run
#
# --dry-run solo hace consultas (GET): muestra qué crearía sin crear ni subir nada.
#
# Hace, en orden y solo si falta:
#   1. Crea el repositorio Git.
#   2. Hace push de la rama main.
#   3. Crea el pipeline a partir de azure-pipelines.yml.
#   4. Crea la política de rama "Build validation" sobre main (bloqueante).
#
# Autenticación (una de las dos):
#   - `az login` con una cuenta que tenga acceso a la organización, o
#   - variable AZURE_DEVOPS_EXT_PAT con un PAT (Code: Read & write, Build: Read & execute,
#     Policy: Read & write... o "Full access").
# El token nunca se escribe en disco ni en la configuración de git.
#
# El proyecto debe existir. El script no borra ni modifica nada que ya exista.
# Sube la rama main tal como está COMMITEADA: los cambios sin commit no viajan.
set -euo pipefail

ORG="${ADO_ORG_URL:-}"
PROJECT="${ADO_PROJECT:-}"
REPO="${ADO_REPO:-$(basename "$(git rev-parse --show-toplevel)")}"
PIPELINE="${ADO_PIPELINE:-}"
DRY=0
BRANCH="main"
YAML="azure-pipelines.yml"
API="7.1"
ADO_RESOURCE="499b84ac-1321-427f-aa17-267ca6975798"   # id público de Azure DevOps en Entra ID
POLITICA_BUILD="0609b952-1397-4640-95ec-e00a01b2c241" # tipo de política "Build"

uso() { sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --org) ORG="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --pipeline) PIPELINE="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) uso 0 ;;
    *) echo "Opción desconocida: $1" >&2; uso 1 ;;
  esac
done
ORG="${ORG%/}"
PIPELINE="${PIPELINE:-$REPO-seguridad}"
[ -n "$ORG" ] && [ -n "$PROJECT" ] || { echo "ERROR: faltan --org y --project." >&2; uso 1; }
for herramienta in git curl python3 base64; do
  command -v "$herramienta" >/dev/null || { echo "ERROR: falta '$herramienta'." >&2; exit 1; }
done
cd "$(git rev-parse --show-toplevel)"
git rev-parse --verify -q "$BRANCH" >/dev/null || { echo "ERROR: no existe la rama $BRANCH." >&2; exit 1; }
[ -f "$YAML" ] || { echo "ERROR: no existe $YAML." >&2; exit 1; }

# ------------------------------------------------------------ autenticación
if [ -n "${AZURE_DEVOPS_EXT_PAT:-}" ]; then
  AUTH="Basic $(printf ':%s' "$AZURE_DEVOPS_EXT_PAT" | base64 | tr -d '\n')"
  echo ">> Autenticando con AZURE_DEVOPS_EXT_PAT"
elif command -v az >/dev/null; then
  TOKEN="$(az account get-access-token --resource "$ADO_RESOURCE" --query accessToken -o tsv)" ||
    { echo "ERROR: no hay sesión de Azure CLI. Ejecuta: ./scripts/ado.sh az login --use-device-code" >&2; exit 1; }
  AUTH="Bearer $TOKEN"
  echo ">> Autenticando con la sesión de az login"
else
  echo "ERROR: define AZURE_DEVOPS_EXT_PAT, o usa Azure CLI: ./scripts/ado.sh az login --use-device-code" >&2
  exit 1
fi

[ "$DRY" = 1 ] && echo ">> MODO --dry-run: solo consultas, no se crea ni se sube nada"
git diff --quiet HEAD 2>/dev/null || echo "AVISO: hay cambios sin commit; solo se sube lo commiteado en $BRANCH." >&2

PROJECT_URL="$ORG/$(python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$PROJECT")"

ado() { # ado METODO URL [cuerpo-json]  -> imprime la respuesta; falla con el error de la API
  local metodo="$1" url="$2" cuerpo="${3:-}" salida codigo
  salida="$(mktemp)"
  if [ -n "$cuerpo" ]; then
    codigo="$(curl -sS -o "$salida" -w '%{http_code}' -X "$metodo" -H "Authorization: $AUTH" \
      -H 'Content-Type: application/json' --data "$cuerpo" "$url")"
  else
    codigo="$(curl -sS -o "$salida" -w '%{http_code}' -X "$metodo" -H "Authorization: $AUTH" "$url")"
  fi
  if [ "$codigo" = 404 ] && [ "$metodo" = GET ]; then rm -f "$salida"; return 4; fi
  if [ "$codigo" -ge 300 ]; then
    echo "ERROR: $metodo $url -> HTTP $codigo" >&2
    head -c 600 "$salida" >&2; echo >&2
    rm -f "$salida"; exit 1
  fi
  cat "$salida"; rm -f "$salida"
}
campo() { python3 -c 'import json,sys; d=json.load(sys.stdin)
for k in sys.argv[1].split("."): d=d[k]
print(d)' "$1"; }

# ------------------------------------------------------------ 0. proyecto
PROJECT_ID="$(ado GET "$ORG/_apis/projects/$(basename "$PROJECT_URL")?api-version=$API" | campo id)" ||
  { echo "ERROR: no se encontró el proyecto '$PROJECT' en $ORG (o no tienes acceso)." >&2; exit 1; }
echo ">> Proyecto: $PROJECT ($PROJECT_ID)"

# ------------------------------------------------------------ 1. repositorio
if REPO_JSON="$(ado GET "$PROJECT_URL/_apis/git/repositories/$REPO?api-version=$API")"; then
  echo ">> Repositorio '$REPO': ya existe"
elif [ "$DRY" = 1 ]; then
  echo ">> Repositorio '$REPO': NO existe -> se crearía"
  REPO_JSON=""
else
  REPO_JSON="$(ado POST "$PROJECT_URL/_apis/git/repositories?api-version=$API" \
    "{\"name\":\"$REPO\",\"project\":{\"id\":\"$PROJECT_ID\"}}")"
  echo ">> Repositorio '$REPO': creado"
fi
REPO_ID=""; REPO_URL="$PROJECT_URL/_git/$REPO"
if [ -n "$REPO_JSON" ]; then
  REPO_ID="$(printf '%s' "$REPO_JSON" | campo id)"
  REPO_URL="$(printf '%s' "$REPO_JSON" | campo remoteUrl | sed -E 's#https://[^@/]+@#https://#')"
fi

# ------------------------------------------------------------ 2. push de main
if [ "$DRY" = 1 ]; then
  echo ">> Rama $BRANCH ($(git rev-parse --short "$BRANCH")): se subiría a $REPO_URL"
else
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "$REPO_URL"
  git -c http.extraheader="AUTHORIZATION: $AUTH" push "$REPO_URL" "$BRANCH:$BRANCH"
  echo ">> Rama $BRANCH publicada en $REPO_URL"
fi

# ------------------------------------------------------------ 3. pipeline
PIPELINE_ID="$(ado GET "$PROJECT_URL/_apis/build/definitions?name=$(python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$PIPELINE")&api-version=$API" |
  python3 -c 'import json,sys; v=json.load(sys.stdin)["value"]; print(v[0]["id"] if v else "")')"
if [ -n "$PIPELINE_ID" ]; then
  echo ">> Pipeline '$PIPELINE': ya existe (id $PIPELINE_ID)"
elif [ "$DRY" = 1 ]; then
  echo ">> Pipeline '$PIPELINE': NO existe -> se crearía desde /$YAML"
else
  PIPELINE_ID="$(ado POST "$PROJECT_URL/_apis/pipelines?api-version=$API" \
    "{\"name\":\"$PIPELINE\",\"folder\":\"\\\\\",\"configuration\":{\"type\":\"yaml\",\"path\":\"/$YAML\",\"repository\":{\"id\":\"$REPO_ID\",\"name\":\"$REPO\",\"type\":\"azureReposGit\"}}}" |
    campo id)"
  echo ">> Pipeline '$PIPELINE': creado (id $PIPELINE_ID)"
fi

# ------------------------------------------------------------ 4. política de PR
if [ -z "$REPO_ID" ] || [ -z "$PIPELINE_ID" ]; then
  echo ">> Política Build validation sobre $BRANCH: se crearía (bloqueante)"
  echo; echo "Fin del --dry-run: no se modificó nada."; exit 0
fi
YA="$(ado GET "$PROJECT_URL/_apis/policy/configurations?repositoryId=$REPO_ID&refName=refs/heads/$BRANCH&policyType=$POLITICA_BUILD&api-version=$API" |
  python3 -c 'import json,sys
pid=int(sys.argv[1])
print(next((str(c["id"]) for c in json.load(sys.stdin)["value"]
            if c.get("settings",{}).get("buildDefinitionId")==pid and not c.get("isDeleted")), ""))' "$PIPELINE_ID")"
if [ -n "$YA" ]; then
  echo ">> Política Build validation sobre $BRANCH: ya existe (id $YA)"
elif [ "$DRY" = 1 ]; then
  echo ">> Política Build validation sobre $BRANCH: NO existe -> se crearía (bloqueante)"
else
  POLITICA_ID="$(ado POST "$PROJECT_URL/_apis/policy/configurations?api-version=$API" "{
    \"isEnabled\": true, \"isBlocking\": true,
    \"type\": {\"id\": \"$POLITICA_BUILD\"},
    \"settings\": {
      \"buildDefinitionId\": $PIPELINE_ID,
      \"displayName\": \"Seguridad: pre-commit, Semgrep y SonarQube\",
      \"queueOnSourceUpdateOnly\": true, \"manualQueueOnly\": false, \"validDuration\": 0,
      \"scope\": [{\"repositoryId\": \"$REPO_ID\", \"refName\": \"refs/heads/$BRANCH\", \"matchKind\": \"exact\"}]
    }}" | campo id)"
  echo ">> Política Build validation sobre $BRANCH: creada (id $POLITICA_ID)"
fi

echo
[ "$DRY" = 1 ] && { echo "Fin del --dry-run: no se modificó nada."; exit 0; }
echo "Listo."
echo "  Repositorio: $PROJECT_URL/_git/$REPO"
echo "  Pipeline:    $PROJECT_URL/_build?definitionId=$PIPELINE_ID"
echo "  Cada pull request a $BRANCH ejecuta el pipeline y no se puede completar si falla."
echo "  Nota: una organización nueva puede no tener paralelismo hospedado gratuito; si el"
echo "  pipeline queda en cola sin agente, solicítalo en https://aka.ms/azpipelines-parallelism-request"
