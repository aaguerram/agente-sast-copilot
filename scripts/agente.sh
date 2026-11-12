#!/usr/bin/env bash
# Punto de entrada único para la terminal (Linux/macOS). En Windows: scripts/agente.ps1.
# Envuelve los scripts del repo; todo corre en contenedores (docker compose).
#
#   ./scripts/agente.sh                     # esta ayuda
#   ./scripts/agente.sh demo                # metodología sobre la app vulnerable + comparación
#   ./scripts/agente.sh rapido              # todas las fases menos SonarQube
#   ./scripts/agente.sh validar             # todas las fases (acepta --solo/--saltar/--listar)
#   ./scripts/agente.sh objetivo objetivos/mi-proyecto
#   ./scripts/agente.sh comparar            # resultados actuales vs. respuesta de referencia
#   ./scripts/agente.sh ado-login
#   ./scripts/agente.sh replicar https://dev.azure.com/ORG PROYECTO          # simulacro
#   ./scripts/agente.sh replicar https://dev.azure.com/ORG PROYECTO --real   # crea y sube
#   ./scripts/agente.sh pipeline seguir --pr 12 [--org URL --project NOM]
#   ./scripts/agente.sh pipeline descargar 55
#
# Subcomandos:
#   ayuda                 Muestra esta ayuda.
#   validar [opciones]    ./scripts/validar-local.sh con las mismas opciones.
#   rapido                Validación sin SonarQube (la fase más lenta).
#   demo [ruta]           Candidatos deterministas de la metodología (pasos 1-3) y SARIF de
#                         Semgrep sobre la ruta (def. agente-sast-g7/samples/app-vulnerable),
#                         y comparación con la referencia esperado/.
#   objetivo <ruta>       Lo mismo que demo sobre un proyecto real (p. ej. objetivos/<p>).
#   comparar              Compara salida/reportes/metodologia/ con la referencia.
#   ado-login             az login --use-device-code (Azure CLI en contenedor).
#   replicar <org> <proy> [--real]
#                         Replica el repo en Azure DevOps. Sin --real solo simula (--dry-run).
#   pipeline <subcomando> ./scripts/ado-pipeline.sh: ejecutar --si | seguir <id>|--pr <n> |
#                         descargar <id> | estado-pr <n>. Org y proyecto: --org/--project o
#                         las variables ADO_ORG_URL y ADO_PROJECT.
#
# Después, en VS Code (Copilot Chat): /demo, /metodologia, /metodologia-paso, /sast, /ayuda.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"
MUESTRA="agente-sast-g7/samples/app-vulnerable"
export UID
GID="$(id -g)"; export GID

uso() { sed -n '2,33p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

py() { # py <script.py> [args] -> Python del contenedor "py" (no se instala nada)
  local tty=(); [ -t 0 ] && [ -t 1 ] || tty=(-T)
  docker compose --profile agentes run --rm "${tty[@]}" py "$@"
}

ruta_relativa() { # normaliza y exige una ruta dentro del repo
  local r="${1%/}"; r="${r#./}"
  case "$r" in
    /*|*..*|"") echo "ERROR: indica una ruta relativa dentro del repo (p. ej. objetivos/mi-proyecto)." >&2; exit 1 ;;
  esac
  [ -d "$r" ] || { echo "ERROR: no existe la carpeta '$r'." >&2; exit 1; }
  printf '%s' "$r"
}

analizar() { # analizar <ruta>: candidatos deterministas + SARIF de Semgrep
  local ruta; ruta="$(ruta_relativa "$1")"
  mkdir -p salida/reportes/metodologia
  echo ">> 1/3 Candidatos de la metodología (pasos 1-3) sobre $ruta"
  py agente-sast-g7/scripts/metodologia.py todo "$ruta" --dir salida/reportes/metodologia
  echo ">> 2/3 Semgrep sobre $ruta"
  OBJETIVO="$ruta" docker compose --profile seguridad run --rm -T semgrep-objetivo
  echo ">> 3/3 Comparación con la referencia"
  py agente-sast-g7/scripts/comparar_esperado.py
  cat <<EOF

Listo. Reportes en salida/reportes/ (semgrep-objetivo.sarif, objetivo-normalizado.json) y
salida/reportes/metodologia/ (candidatos-*.json).
Siguiente paso, en VS Code con Copilot Chat:
  /metodologia $ruta        (los 8 pasos con razonamiento + informe)
  /sast salida/reportes/semgrep-objetivo.sarif
EOF
}

cmd="${1:-ayuda}"; [ $# -gt 0 ] && shift
case "$cmd" in
  ayuda|help|-h|--help) uso 0 ;;
  validar) exec bash scripts/validar-local.sh "$@" ;;
  rapido) exec bash scripts/validar-local.sh --saltar sonarqube "$@" ;;
  demo) analizar "${1:-$MUESTRA}" ;;
  objetivo)
    [ $# -ge 1 ] || { echo "Uso: ./scripts/agente.sh objetivo objetivos/<proyecto>" >&2; exit 1; }
    analizar "$1" ;;
  comparar) py agente-sast-g7/scripts/comparar_esperado.py "$@" ;;
  ado-login) exec bash scripts/ado.sh az login --use-device-code ;;
  replicar)
    [ $# -ge 2 ] || { echo "Uso: ./scripts/agente.sh replicar https://dev.azure.com/ORG PROYECTO [--real]" >&2; exit 1; }
    org="$1"; proy="$2"; shift 2
    modo=(--dry-run)
    if [ "${1:-}" = "--real" ]; then modo=(); shift; fi
    exec bash scripts/ado.sh ./scripts/ado-bootstrap.sh --org "$org" --project "$proy" "${modo[@]}" "$@" ;;
  pipeline)
    [ $# -ge 1 ] || { echo "Uso: ./scripts/agente.sh pipeline seguir --pr <n> | descargar <id> | estado-pr <n> | ejecutar --si" >&2; exit 1; }
    exec bash scripts/ado.sh ./scripts/ado-pipeline.sh "$@" ;;
  *) echo "Subcomando desconocido: $cmd" >&2; uso 1 ;;
esac
