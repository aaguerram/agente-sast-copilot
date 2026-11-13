#!/usr/bin/env bash
# Ejecuta en local TODAS las fases de prueba del repositorio, en contenedores
# (docker compose). Solo necesita git y Docker: no instala nada en la máquina.
#
#   ./scripts/validar-local.sh                    # todas las fases
#   ./scripts/validar-local.sh --saltar sonarqube # todas menos SonarQube (es la más lenta)
#   ./scripts/validar-local.sh --solo semgrep,api
#   ./scripts/validar-local.sh --listar
#
# Fases (mismo orden y versiones que azure-pipelines.yml, más docs y la API):
#   pre-commit    hooks de .pre-commit-config.yaml (incluye gitleaks y los hooks .NET)
#   hooks-tests   pruebas de los hooks .NET propios (tools/pre-commit-hooks/tests)
#   gitleaks      secretos en todo el historial de git
#   semgrep       Semgrep CE bloqueante (registro + reglas de .semgrep/)
#   semgrep-demo  reporte con hallazgos sobre la muestra vulnerable + normalización
#   metodologia   pruebas de metodologia.py + candidatos de la metodología SAST sobre app-vulnerable
#   sonarqube     SonarQube Community efímero sobre rickmorty-clean
#   docs          sitio MkDocs en modo estricto (salida/sitio.zip)
#   api           build de la imagen de rickmorty-clean y prueba de humo de sus endpoints
#
# Reportes:  salida/reportes/   (SARIF, JSON normalizado, logs/<fase>.log, resumen.md)
# Salida:    0 si todas las fases pasan, 1 si alguna falla.
#
# Variables opcionales: COMPOSE_PROJECT_NAME (aislar una corrida), SONAR_PORT (def. 9100),
# API_PORT_SMOKE (primer puerto a probar para la API; por defecto 18080, busca el siguiente libre),
# SIN_INTERNET=1 (máquina sin internet: la fase api usa la imagen ya cargada, no la reconstruye).
set -uo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ" || exit 1

TODAS=(pre-commit hooks-tests gitleaks semgrep semgrep-demo metodologia sonarqube docs api)
SOLO=""; SALTAR=""
uso() { sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }
while [ $# -gt 0 ]; do
  case "$1" in
    --solo) SOLO=",$2,"; shift 2 ;;
    --saltar) SALTAR=",$2,"; shift 2 ;;
    --listar) printf '%s\n' "${TODAS[@]}"; exit 0 ;;
    -h|--help) uso 0 ;;
    *) echo "Opción desconocida: $1" >&2; uso 1 ;;
  esac
done

# ------------------------------------------------------------ prerequisitos
command -v docker >/dev/null || { echo "ERROR: falta Docker." >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERROR: falta el plugin 'docker compose'." >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "ERROR: Docker no responde (¿servicio arriba? ¿tu usuario está en el grupo docker?)." >&2; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
  { echo "ERROR: $RAIZ no es un repositorio git (pre-commit y gitleaks lo necesitan). Clónalo con git." >&2; exit 1; }

# ------------------------------------------------------------ entorno del host
# Nada de valores fijos de una máquina concreta: todo se detecta aquí.
export UID
GID="$(id -g)"; export GID
SOCK=/var/run/docker.sock
DOCKER_GID="$(stat -c %g "$SOCK" 2>/dev/null || stat -f %g "$SOCK" 2>/dev/null || echo 0)"; export DOCKER_GID
# Docker Desktop (macOS): dentro de la VM el socket solo lo usa root.
[ "$(uname -s)" = Darwin ] && export SONAR_RUN_USER="${SONAR_RUN_USER:-0:0}" DOCKER_GID=0
REPORTES="$RAIZ/salida/reportes"; LOGS="$REPORTES/logs"
# Se crean con tu usuario ANTES de montarlos (si los crea Docker, quedan de root).
mkdir -p "$REPORTES" "$LOGS"
PROYECTO="${COMPOSE_PROJECT_NAME:-agente-pruebas-copilot}"
DC=(docker compose -p "$PROYECTO")

# Construye la imagen de un servicio solo si falta: con las imágenes ya cargadas
# (docker load) no se toca la red. Tras cambiar un Dockerfile: docker compose --profile "*" build
asegurar_imagen() { # asegurar_imagen <imagen> <servicio>
  docker image inspect "$1" >/dev/null 2>&1 || "${DC[@]}" --profile "*" build -q "$2"
}

# ------------------------------------------------------------ fases
fase_pre-commit()   { "${DC[@]}" --profile seguridad run --rm pre-commit; }
fase_hooks-tests()  { "${DC[@]}" --profile seguridad run --rm pre-commit-hooks-tests; }
fase_gitleaks()     { "${DC[@]}" --profile seguridad run --rm gitleaks; }
fase_semgrep()      { "${DC[@]}" --profile seguridad run --rm semgrep; }
fase_semgrep-demo() {
  rm -f "$REPORTES/muestras-normalizado.json"
  "${DC[@]}" --profile seguridad run --rm semgrep-demo &&
    python_ok="$(grep -c '"regla"' "$REPORTES/muestras-normalizado.json" 2>/dev/null || echo 0)" &&
    echo ">> Hallazgos normalizados en la muestra: $python_ok" &&
    [ "$python_ok" -gt 0 ]
}
fase_metodologia() {
  local py=("${DC[@]}" --profile agentes run --rm -T py)
  "${py[@]}" agente-sast-g7/scripts/tests/test_metodologia.py &&
    "${py[@]}" agente-sast-g7/scripts/tests/test_kb.py &&
    "${py[@]}" agente-sast-g7/scripts/metodologia.py todo agente-sast-g7/samples/app-vulnerable \
      --dir salida/reportes/metodologia
}
fase_sonarqube() {
  # El SDK con el scanner y la caché de NuGet lo lanza sonar-analizar.sh como contenedor hermano.
  asegurar_imagen agente-pruebas-copilot-dotnet dotnet-objetivo &&
    "${DC[@]}" --profile seguridad run --rm sonarqube
}
fase_docs() {
  local habia; habia="$("${DC[@]}" ps -q plantuml 2>/dev/null)"
  "${DC[@]}" --profile tools run --rm docs-build; local rc=$?
  # Si plantuml lo levantó esta corrida, se baja; si ya estaba (sitio en vivo), se deja.
  [ -n "$habia" ] || "${DC[@]}" rm -sf plantuml >/dev/null 2>&1
  return $rc
}
puerto_libre() {
  local p="${API_PORT_SMOKE:-18080}"
  while (exec 3<>"/dev/tcp/127.0.0.1/$p") 2>/dev/null; do p=$((p + 1)); done
  echo "$p"
}
fase_api() {
  local proy="${PROYECTO}-api-smoke" puerto rc=0
  puerto="$(puerto_libre)"
  local api=(docker compose -p "$proy" -f rickmorty-clean/docker-compose.yml)
  local construir=(--build)
  if [ "${SIN_INTERNET:-0}" = 1 ]; then
    construir=(); echo ">> SIN_INTERNET=1: se usa la imagen rickmorty-clean-api ya cargada (no se reconstruye)"
  fi
  echo ">> Levantando rickmorty-clean en el puerto $puerto (proyecto $proy)"
  API_PORT="$puerto" "${api[@]}" up -d "${construir[@]}" --wait --wait-timeout 180 || {
    rc=1
    [ ${#construir[@]} = 0 ] || echo "   Si esta máquina no tiene internet, repite con SIN_INTERNET=1 (usa la imagen ya cargada)."
  }
  if [ $rc = 0 ]; then
    # La prueba corre en UN contenedor de la misma red: no depende de curl en el host.
    asegurar_imagen agente-pruebas-copilot-python py &&
      docker run --rm --network "${proy}_default" -v "$RAIZ/scripts/api_humo.py:/api_humo.py:ro" \
        agente-pruebas-copilot-python python /api_humo.py http://api:8080 || rc=1
  fi
  [ $rc = 0 ] || API_PORT="$puerto" "${api[@]}" logs --tail 40 2>&1 | sed 's/^/   /'
  # La imagen rickmorty-clean-api se conserva: la siguiente corrida reutiliza sus capas y sin internet no se podría reconstruir.
  API_PORT="$puerto" "${api[@]}" down -v >/dev/null 2>&1
  return $rc
}

# ------------------------------------------------------------ ejecución
declare -A RESULTADO DURACION
FALLAS=0
for f in "${TODAS[@]}"; do
  if [ -n "$SOLO" ] && [[ "$SOLO" != *",$f,"* ]]; then RESULTADO[$f]="omitida"; continue; fi
  if [[ "$SALTAR" == *",$f,"* ]]; then RESULTADO[$f]="omitida"; continue; fi
  echo
  echo "==================== $f"
  inicio=$SECONDS
  if "fase_$f" 2>&1 | tee "$LOGS/$f.log"; then
    RESULTADO[$f]="OK"
  else
    RESULTADO[$f]="FALLA"; FALLAS=$((FALLAS + 1))
  fi
  DURACION[$f]=$((SECONDS - inicio))
done

# ------------------------------------------------------------ resumen
{
  echo "# Validación local — $(date '+%Y-%m-%d %H:%M')"
  echo
  echo "Commit: \`$(git rev-parse --short HEAD 2>/dev/null || echo sin-commit)\`$(git diff --quiet 2>/dev/null || echo ' (con cambios sin commit)')"
  echo
  echo "| Fase | Resultado | Duración | Log |"
  echo "|---|---|---|---|"
  for f in "${TODAS[@]}"; do
    d="${DURACION[$f]:-}"; [ -n "$d" ] && d="${d}s" || d="-"
    echo "| $f | ${RESULTADO[$f]} | $d | \`salida/reportes/logs/$f.log\` |"
  done
  echo
  echo "Reportes: \`salida/reportes/\` (gitleaks.sarif, semgrep.sarif, semgrep-muestras.sarif, muestras-normalizado.json, sonar.sarif, metodologia/candidatos-*.json)."
} > "$REPORTES/resumen.md"

echo
echo "==================== RESUMEN"
printf '%-14s %s\n' FASE RESULTADO
for f in "${TODAS[@]}"; do printf '%-14s %s\n' "$f" "${RESULTADO[$f]}"; done
echo "Detalle: salida/reportes/resumen.md"
[ "$FALLAS" = 0 ] || { echo "$FALLAS fase(s) con FALLA." >&2; exit 1; }
echo "Todas las fases ejecutadas pasaron."
