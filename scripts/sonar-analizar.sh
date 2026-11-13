#!/usr/bin/env bash
# Analiza la solución .NET con SonarQube Community y exporta los hallazgos.
# Es el MISMO script en local y en el pipeline (azure-pipelines.yml).
#
#   ./scripts/sonar-analizar.sh
#
# Sin SONAR_HOST_URL levanta un SonarQube efímero en Docker (no guarda historial),
# analiza y lo elimina. Con SONAR_HOST_URL + SONAR_TOKEN usa un servidor real.
#
# Variables (todas opcionales):
#   SONAR_HOST_URL      URL de un SonarQube existente. Vacío = servidor efímero.
#   SONAR_TOKEN         Token de análisis del servidor existente (secreto).
#   SONAR_PROJECT_KEY   Clave del proyecto            (def. rickmorty-clean)
#   SONAR_SOLUTION      Solución a analizar           (def. rickmorty-clean/RickMorty.sln)
#   SONAR_FAIL_ON       Severidades que bloquean      (def. BLOCKER,CRITICAL; vacío = no bloquea)
#   SONAR_PORT          Puerto local del efímero      (def. 9000)
#   SONAR_IMAGE         Imagen del servidor           (def. sonarqube:community)
#   SONAR_SCANNER_VERSION  dotnet-sonarscanner        (def. 12.1.0)
#   DOTNET_SDK_IMAGE    SDK si no hay dotnet local    (def. mcr.microsoft.com/dotnet/sdk:10.0;
#                       docker compose usa agente-pruebas-copilot-dotnet, que ya trae el
#                       scanner y los paquetes NuGet: el análisis no necesita internet)
#   SONAR_ADMIN_USER / SONAR_ADMIN_PASSWORD  Cuenta inicial del efímero (def. admin / admin)
#   SONAR_KEEP=1        No elimina el servidor efímero al terminar (para abrir la UI)
#   REPORTES_DIR        Carpeta de salida             (def. reportes)
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"

PROJECT_KEY="${SONAR_PROJECT_KEY:-rickmorty-clean}"
SOLUTION="${SONAR_SOLUTION:-rickmorty-clean/RickMorty.sln}"
FAIL_ON="${SONAR_FAIL_ON-BLOCKER,CRITICAL}"
PORT="${SONAR_PORT:-9000}"
IMAGE="${SONAR_IMAGE:-sonarqube:community}"
SCANNER_VERSION="${SONAR_SCANNER_VERSION:-12.1.0}"
SDK_IMAGE="${DOTNET_SDK_IMAGE:-mcr.microsoft.com/dotnet/sdk:10.0}"
REPORTES="${REPORTES_DIR:-reportes}"
CONTENEDOR="sonarqube-efimero-$$-$RANDOM"   # $$ es 1 dentro de un contenedor: se añade $RANDOM
RED="sonarqube-red-${CONTENEDOR#sonarqube-efimero-}"
EFIMERO=0
# Cuenta inicial que trae la imagen; solo se usa contra el servidor efímero.
ADMIN="${SONAR_ADMIN_USER:-admin}:${SONAR_ADMIN_PASSWORD:-admin}"
HOST_URL="${SONAR_HOST_URL:-}"
TOKEN="${SONAR_TOKEN:-}"

mkdir -p "$REPORTES"

# ¿Corre dentro de un contenedor (servicio "sonarqube" de docker compose)? Entonces no
# se usa la red ni las rutas del host: este contenedor se une a la red del servidor
# efímero y el SDK hereda el montaje del repo con --volumes-from. Así funciona igual en
# Linux y en Docker Desktop (Windows/macOS), donde la ruta del host es C:\... y no existe
# network_mode: host. Fuera de un contenedor (pipeline) se usa localhost y -v "$RAIZ".
YO=""
if [ -f /.dockerenv ] && docker inspect "$(hostname)" >/dev/null 2>&1; then
  YO="$(hostname)"
fi

limpiar() {
  if [ "$EFIMERO" = 1 ] && [ "${SONAR_KEEP:-0}" != 1 ]; then
    docker rm -f "$CONTENEDOR" >/dev/null 2>&1 || true
    [ -n "$YO" ] && docker network disconnect -f "$RED" "$YO" >/dev/null 2>&1
    docker network rm "$RED" >/dev/null 2>&1 || true
  fi
}
trap limpiar EXIT

export SONAR_EXPORT_TOKEN=""
api() { # $1 = ruta de la API web de SonarQube
  curl -fsS -H "Authorization: Bearer ${TOKEN}" "${HOST_URL}$1"
}

# ---------------------------------------------------------------- servidor
if [ -z "$HOST_URL" ]; then
  EFIMERO=1
  echo ">> Levantando SonarQube efímero ($IMAGE) en el puerto $PORT"
  docker network create "$RED" >/dev/null
  docker run -d --name "$CONTENEDOR" --network "$RED" -p "${PORT}:9000" \
    -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true "$IMAGE" >/dev/null
  if [ -n "$YO" ]; then
    docker network connect "$RED" "$YO"
    HOST_URL="http://${CONTENEDOR}:9000"
  else
    HOST_URL="http://localhost:${PORT}"
  fi

  echo -n ">> Esperando a que SonarQube esté UP"
  for i in $(seq 1 120); do
    estado="$(curl -fsS "${HOST_URL}/api/system/status" 2>/dev/null | sed -n 's/.*"status":"\([A-Z_]*\)".*/\1/p' || true)"
    [ "$estado" = "UP" ] && break
    if [ "$i" = 120 ]; then
      echo; echo "ERROR: SonarQube no arrancó en 10 minutos (estado: ${estado:-sin respuesta})." >&2
      docker logs --tail 40 "$CONTENEDOR" >&2 || true
      exit 1
    fi
    echo -n "."; sleep 5
  done
  echo " listo"

  # Token de análisis con la cuenta inicial del contenedor recién creado.
  TOKEN="$(curl -fsS --user "$ADMIN" -X POST \
    "${HOST_URL}/api/user_tokens/generate?name=pipeline-$$" |
    sed -n 's/.*"token":"\([^"]*\)".*/\1/p')"
  [ -n "$TOKEN" ] || { echo "ERROR: no se pudo generar el token de análisis." >&2; exit 1; }
elif [ -z "$TOKEN" ]; then
  echo "ERROR: SONAR_HOST_URL está definido pero falta SONAR_TOKEN." >&2
  exit 1
else
  echo ">> Usando el servidor SonarQube $HOST_URL"
fi

# ---------------------------------------------------------------- análisis
# Comandos del scanner: begin -> build -> end (espera el quality gate del servidor).
ANALISIS='
set -e
export PATH="$PATH:$HOME/.dotnet/tools"
# La imagen agente-pruebas-copilot-dotnet ya trae el scanner: no se descarga nada.
command -v dotnet-sonarscanner >/dev/null 2>&1 ||
  dotnet tool update --global dotnet-sonarscanner --version "$SCANNER_VERSION" >/dev/null
dotnet sonarscanner begin /k:"$PROJECT_KEY" /n:"$PROJECT_KEY" \
  /d:sonar.host.url="$SCAN_URL" /d:sonar.token="$TOKEN" \
  /d:sonar.qualitygate.wait=true /d:sonar.qualitygate.timeout=300 \
  /d:sonar.inclusions="**/*.cs" /d:sonar.exclusions="**/bin/**,**/obj/**,salida/**,objetivos/**,agente-sast-g7/samples/**"
dotnet build "$SOLUTION" --no-incremental -nologo -v:minimal
dotnet sonarscanner end /d:sonar.token="$TOKEN"
'

GATE=0
if command -v dotnet >/dev/null 2>&1 && dotnet --list-sdks | grep -q '^10\.'; then
  echo ">> Analizando con el SDK de .NET instalado"
  SCAN_URL="$HOST_URL" TOKEN="$TOKEN" PROJECT_KEY="$PROJECT_KEY" SOLUTION="$SOLUTION" \
    SCANNER_VERSION="$SCANNER_VERSION" bash -c "$ANALISIS" || GATE=$?
else
  echo ">> Sin .NET 10 local: analizando dentro de $SDK_IMAGE"
  if [ "$EFIMERO" = 1 ]; then
    RED_ARGS=(--network "$RED"); SCAN_URL="http://${CONTENEDOR}:9000"
  else
    RED_ARGS=(--network host); SCAN_URL="$HOST_URL"
  fi
  if [ -n "$YO" ]; then
    SRC_ARGS=(--volumes-from "$YO" -w "$RAIZ")   # mismo montaje que este contenedor
  else
    SRC_ARGS=(-v "$RAIZ":/src -w /src)
  fi
  docker run --rm "${RED_ARGS[@]}" -u "$(id -u):$(id -g)" \
    -e HOME=/tmp -e DOTNET_CLI_HOME=/tmp -e DOTNET_NOLOGO=1 \
    -e SCAN_URL="$SCAN_URL" -e TOKEN="$TOKEN" -e PROJECT_KEY="$PROJECT_KEY" \
    -e SOLUTION="$SOLUTION" -e SCANNER_VERSION="$SCANNER_VERSION" \
    "${SRC_ARGS[@]}" "$SDK_IMAGE" bash -c "$ANALISIS" || GATE=$?
fi

# ---------------------------------------------------------------- exportación
if [ "$GATE" != 0 ] && ! api "/api/components/show?component=${PROJECT_KEY}" >/dev/null 2>&1; then
  echo "ERROR: el análisis de SonarQube falló antes de publicar resultados (código $GATE)." >&2
  exit 1
fi

echo ">> Exportando hallazgos a $REPORTES/"
export SONAR_EXPORT_TOKEN="$TOKEN"
BLOQUEA=0
python3 "$RAIZ/scripts/sonar_a_sarif.py" \
  --host-url "$HOST_URL" --project-key "$PROJECT_KEY" --fail-on "$FAIL_ON" \
  --salida "$REPORTES" || BLOQUEA=$?

if [ "${SONAR_KEEP:-0}" = 1 ] && [ "$EFIMERO" = 1 ]; then
  echo ">> SonarQube sigue arriba en http://localhost:${PORT} (usuario admin / admin). Para eliminarlo:"
  echo "   docker rm -f $CONTENEDOR && docker network rm $RED"
fi

if [ "$GATE" != 0 ]; then
  echo "ERROR: el análisis o el quality gate de SonarQube falló (código $GATE)." >&2
  exit 1
fi
if [ "$BLOQUEA" != 0 ]; then
  echo "ERROR: hay hallazgos con severidad bloqueante ($FAIL_ON). Ver $REPORTES/sonar.sarif" >&2
  exit 1
fi
echo ">> SonarQube: análisis correcto, sin hallazgos bloqueantes."
