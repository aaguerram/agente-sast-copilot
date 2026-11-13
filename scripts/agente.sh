#!/usr/bin/env bash
# Punto de entrada único para la terminal (Linux/macOS). En Windows: scripts/agente.ps1.
# Envuelve los scripts del repo; todo corre en contenedores (docker compose).
#
#   ./scripts/agente.sh                     # esta ayuda
#   ./scripts/agente.sh demo                # metodología sobre la app vulnerable + comparación
#   ./scripts/agente.sh rapido              # todas las fases menos SonarQube
#   ./scripts/agente.sh validar             # todas las fases (acepta --solo/--saltar/--listar)
#   ./scripts/agente.sh objetivo objetivos/mi-proyecto
#   ./scripts/agente.sh objetivo objetivos/mi-proyecto --sin-dotnet   # solo código, sin compilar
#   ./scripts/agente.sh dotnet objetivos/mi-proyecto   # solo los analizadores .NET
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
#   demo [ruta] [--sin-dotnet]
#                         Candidatos deterministas de la metodología (pasos 1-3), SARIF de
#                         Semgrep y de los analizadores de seguridad .NET sobre la ruta
#                         (def. agente-sast-g7/samples/app-vulnerable), y comparación con la
#                         referencia esperado/.
#   objetivo <ruta> [--sin-dotnet]
#                         Lo mismo que demo sobre un proyecto real (p. ej. objetivos/<p>).
#       --sin-dotnet      No ejecuta los analizadores .NET: es el único paso que COMPILA el
#                         proyecto (necesita sus paquetes NuGet). Sin él basta el código
#                         fuente. Con SIN_INTERNET=1 (máquina sin internet) se omite solo.
#   dotnet [ruta]         Analizadores de seguridad .NET (CA2100, CA3001-CA3012, CA5350…)
#                         sobre la ruta: compila cada .csproj y normaliza el SARIF con
#                         CWE/OWASP de la KB (def. agente-sast-g7/samples/app-vulnerable).
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

uso() { sed -n '2,44p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

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

# Analizadores .NET + normalización. Es el único paso que COMPILA el objetivo.
pasos_dotnet() { # pasos_dotnet <ruta ya validada>
  local ruta="$1"
  mkdir -p salida/reportes
  # Se borra el resultado anterior: si el paso falla no queda el de otro proyecto.
  rm -f salida/reportes/dotnet-normalizado.json
  OBJETIVO="$ruta" docker compose --profile seguridad run --rm -T dotnet-objetivo &&
    py agente-sast-g7/scripts/normalizar_sarif.py salida/reportes/dotnet-objetivo/*.sarif \
      --base /tmp/src --prefijo "$ruta" -o salida/reportes/dotnet-normalizado.json
}

# analizar [ruta] [--sin-dotnet]: candidatos deterministas + SARIF de Semgrep y de .NET
analizar() {
  local arg ruta="" sin_dotnet=0 motivo="" dotnet_ok=0 extra=""
  for arg in "$@"; do
    case "$arg" in
      --sin-dotnet) sin_dotnet=1 ;;
      -*) echo "Opción desconocida: $arg (usa --sin-dotnet)." >&2; exit 1 ;;
      *) [ -z "$ruta" ] || { echo "ERROR: indica una sola ruta." >&2; exit 1; }; ruta="$arg" ;;
    esac
  done
  ruta="$(ruta_relativa "${ruta:-$MUESTRA}")"
  mkdir -p salida/reportes/metodologia
  echo ">> 1/4 Candidatos de la metodología (pasos 1-3) sobre $ruta"
  py agente-sast-g7/scripts/metodologia.py todo "$ruta" --dir salida/reportes/metodologia
  echo ">> 2/4 Semgrep sobre $ruta"
  OBJETIVO="$ruta" docker compose --profile seguridad run --rm -T semgrep-objetivo

  # Paso opcional: no detiene el análisis si se omite o si el proyecto no compila.
  if [ "$sin_dotnet" = 1 ]; then
    motivo="--sin-dotnet"
  elif [ "${SIN_INTERNET:-0}" = 1 ]; then
    motivo="SIN_INTERNET=1: compilar necesita los paquetes NuGet del proyecto"
  elif [ -z "$(find "$ruta" -name '*.csproj' -not -path '*/bin/*' -not -path '*/obj/*' -print -quit)" ]; then
    motivo="no hay ningún .csproj en $ruta"
  fi
  if [ -n "$motivo" ]; then
    rm -f salida/reportes/dotnet-normalizado.json
    echo ">> 3/4 Analizadores de seguridad .NET: omitido ($motivo)"
  else
    echo ">> 3/4 Analizadores de seguridad .NET sobre $ruta (compila el proyecto; --sin-dotnet lo omite)"
    if pasos_dotnet "$ruta"; then
      dotnet_ok=1; extra=", dotnet-normalizado.json"
    else
      echo "AVISO: los analizadores .NET no terminaron (¿el proyecto compila?, ¿faltan paquetes NuGet?). El análisis sigue sin esa fuente." >&2
    fi
  fi

  echo ">> 4/4 Comparación con la referencia"
  py agente-sast-g7/scripts/comparar_esperado.py
  cat <<FIN

Listo. Reportes en salida/reportes/ (semgrep-objetivo.sarif, objetivo-normalizado.json$extra) y
salida/reportes/metodologia/ (candidatos-*.json).
Siguiente paso, en VS Code con Copilot Chat:
  /metodologia $ruta        (los 8 pasos con razonamiento + informe)
  /sast salida/reportes/semgrep-objetivo.sarif
FIN
  [ "$dotnet_ok" = 0 ] || echo "  /sast salida/reportes/dotnet-normalizado.json"
}

analizar_dotnet() { # analizar_dotnet <ruta>: solo los analizadores .NET + normalización
  local ruta; ruta="$(ruta_relativa "$1")"
  echo ">> Analizadores de seguridad .NET sobre $ruta (dotnet build en contenedor) + normalización"
  pasos_dotnet "$ruta"
  echo "Siguiente paso, en Copilot Chat: /sast salida/reportes/dotnet-normalizado.json"
}

cmd="${1:-ayuda}"; [ $# -gt 0 ] && shift
case "$cmd" in
  ayuda|help|-h|--help) uso 0 ;;
  validar) exec bash scripts/validar-local.sh "$@" ;;
  rapido) exec bash scripts/validar-local.sh --saltar sonarqube "$@" ;;
  demo) analizar "$@" ;;
  objetivo)
    [ $# -ge 1 ] && [ "$1" != --sin-dotnet ] ||
      { echo "Uso: ./scripts/agente.sh objetivo objetivos/<proyecto> [--sin-dotnet]" >&2; exit 1; }
    analizar "$@" ;;
  dotnet) analizar_dotnet "${1:-$MUESTRA}" ;;
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
