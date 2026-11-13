#!/usr/bin/env bash
# Lleva TODAS las imágenes del repo a una máquina sin internet (Linux/macOS).
# En Windows: scripts/imagenes.ps1. Guía paso a paso: exportar-imagenes-offline.md.
#
#   ./scripts/imagenes.sh exportar [archivo]   # máquina CON internet: construye, descarga y guarda
#   ./scripts/imagenes.sh cargar [archivo]     # máquina SIN internet: docker load + verificación
#   ./scripts/imagenes.sh verificar            # comprueba que no falta ninguna imagen
#   ./scripts/imagenes.sh listar               # imágenes que usa el repo
#
# El archivo por defecto es imagenes-sast.tar en la raíz del repo (no se versiona).
# Las imágenes ya traen las reglas de Semgrep, los hooks de pre-commit, el scanner de
# SonarQube y los paquetes NuGet: en la máquina destino no se descarga nada.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"
export UID
GID="$(id -g)"; export GID
DC=(docker compose --profile "*")

uso() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }
imagenes() { "${DC[@]}" config --images | sort -u; }

verificar() {
  local faltan=0 img
  while IFS= read -r img; do
    if docker image inspect "$img" >/dev/null 2>&1; then echo "   OK     $img"
    else echo "   FALTA  $img"; faltan=$((faltan + 1)); fi
  done < <(imagenes)
  [ "$faltan" = 0 ] || { echo "ERROR: faltan $faltan imagen(es)." >&2; return 1; }
  echo "Todas las imágenes están en esta máquina: se puede trabajar sin internet."
}

cmd="${1:-ayuda}"; [ $# -gt 0 ] && shift
ARCHIVO="${1:-imagenes-sast.tar}"
case "$cmd" in
  ayuda|help|-h|--help) uso 0 ;;
  listar) imagenes ;;
  verificar) verificar ;;
  exportar)
    echo ">> 1/3 Construyendo las imágenes propias (tools/ y rickmorty-clean)"
    "${DC[@]}" build
    echo ">> 2/3 Descargando las imágenes de registro"
    "${DC[@]}" pull --ignore-buildable
    echo ">> 3/3 Guardando en $ARCHIVO"
    verificar >/dev/null
    mapfile -t lista < <(imagenes)
    docker save -o "$ARCHIVO" "${lista[@]}"
    echo "Listo: $ARCHIVO ($(du -h "$ARCHIVO" | cut -f1), ${#lista[@]} imágenes). Cópialo junto con el repo a la máquina sin internet y allí: ./scripts/imagenes.sh cargar"
    ;;
  cargar)
    [ -f "$ARCHIVO" ] || { echo "ERROR: no existe $ARCHIVO" >&2; exit 1; }
    docker load -i "$ARCHIVO"
    verificar
    ;;
  *) echo "Subcomando desconocido: $cmd" >&2; uso 1 ;;
esac
