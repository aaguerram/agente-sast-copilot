#!/usr/bin/env bash
# Ejecuta un comando dentro del contenedor de Azure CLI (servicio "ado" de docker-compose.yml),
# para no instalar az en la máquina. La sesión de az se guarda en ~/.azure del host.
#
#   ./scripts/ado.sh az login --use-device-code
#   ./scripts/ado.sh az devops configure --defaults organization=https://dev.azure.com/ORG
#   ./scripts/ado.sh ./scripts/ado-bootstrap.sh --org https://dev.azure.com/ORG --project PROY --dry-run
#   ./scripts/ado.sh            # shell interactiva
#
# Un PAT, si lo usas, va SOLO en la variable de entorno AZURE_DEVOPS_EXT_PAT del host
# (por ejemplo: read -rs AZURE_DEVOPS_EXT_PAT && export AZURE_DEVOPS_EXT_PAT). Nunca en archivos.
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"
export UID
GID="$(id -g)"; export GID
# Dentro del contenedor el repo está en /repo: se pasa su nombre real (ado-bootstrap.sh y
# ado-pipeline.sh lo usan como nombre del repositorio y del pipeline).
export ADO_REPO="${ADO_REPO:-$(basename "$RAIZ")}"
export AZURE_CONFIG_HOST="${AZURE_CONFIG_HOST:-$HOME/.azure}"
mkdir -p "$AZURE_CONFIG_HOST"      # con tu usuario; si lo crea Docker queda de root
TTY=(); [ -t 0 ] && [ -t 1 ] || TTY=(-T)
# Un script .sh se lanza con bash: en montajes desde Windows (NTFS) el bit +x no viaja.
if [ $# -gt 0 ] && [[ "$1" == *.sh ]]; then set -- bash "$@"; fi
exec docker compose --profile ado run --rm "${TTY[@]}" ado "${@:-bash}"
