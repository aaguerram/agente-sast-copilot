#!/usr/bin/env python3
"""Prueba de humo de la API de rickmorty-clean (fase "api" de validar-local).

    python api_humo.py http://api:8080

Espera a que la API responda y comprueba el código HTTP de cada ruta. Corre en UN solo
contenedor de la misma red que la API (imagen agente-pruebas-copilot-python): no depende
de curl en el host ni de internet. Solo stdlib. Salida: 0 si todo coincide, 1 si no.
"""
from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request

RUTAS = [
    ("/api/characters", 200), ("/api/characters/1", 200), ("/api/locations", 200),
    ("/api/locations/1", 200), ("/api/locations/1/residents", 200), ("/api/episodes", 200),
    ("/api/episodes/1", 200), ("/api/episodes/1/characters", 200), ("/api/characters/999999", 404),
]
ESPERA_S = 60


def codigo(url: str) -> int:
    """Código HTTP de la URL; 0 si no hubo respuesta."""
    try:
        # La URL base la pasa validar-local (red interna de docker) y main() solo admite http(s).
        # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, OSError):
        return 0


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    base = sys.argv[1].rstrip("/")
    if not base.startswith(("http://", "https://")):
        print("ERROR: la URL base debe empezar por http:// o https://", file=sys.stderr)
        return 2
    limite = time.monotonic() + ESPERA_S
    while codigo(base + RUTAS[0][0]) == 0 and time.monotonic() < limite:
        time.sleep(1)
    fallas = 0
    for ruta, esperado in RUTAS:
        c = codigo(base + ruta)
        if c == esperado:
            print(f"   OK    {c} {ruta}")
        else:
            print(f"   FALLA {c} {ruta} (esperado {esperado})")
            fallas += 1
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
