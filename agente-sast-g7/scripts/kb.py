#!/usr/bin/env python3
"""Consulta de la base de conocimiento del agente (agente-sast-g7/kb/), sin red.

    from kb import normalizar_cwe, buscar_cwe, owasp_de, cheatsheets_de

Línea de comandos (Docker):
    docker compose --profile agentes run --rm py agente-sast-g7/scripts/kb.py CWE-89 CWE-639
"""
from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from pathlib import Path

KB_DIR = Path(__file__).resolve().parents[1] / "kb"
_CWE = re.compile(r"CWE[\s_:\-]*(\d+)", re.IGNORECASE)


def normalizar_cwe(texto) -> str:
    """'CWE-798: Use of Hard-coded Credentials' | 'cwe_89' | 89 → 'CWE-798' | 'CWE-89'; '' si no hay."""
    if texto is None:
        return ""
    if isinstance(texto, int) or str(texto).strip().isdigit():
        return f"CWE-{int(texto)}"
    m = _CWE.search(str(texto))
    return f"CWE-{int(m.group(1))}" if m else ""


@lru_cache(maxsize=None)
def _cargar(nombre: str) -> dict:
    f = KB_DIR / nombre
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def catalogo() -> dict:
    return _cargar("cwe-owasp.json").get("cwe", {})


def buscar_cwe(cwe) -> dict | None:
    """Entrada de la KB para un CWE (acepta etiquetas completas), o None si no existe."""
    return catalogo().get(normalizar_cwe(cwe))


def owasp_de(cwe, version: str = "2021", heredar: bool = True) -> str:
    """Categoría OWASP Top 10 oficial (vista de MITRE) de un CWE.

    Si el CWE no está mapeado y heredar=True, sube por sus padres (ChildOf primario).
    Si pertenece a varias categorías, devuelve la primera. '' si no hay mapeo."""
    campo = "owasp_2021" if version == "2021" else "owasp_2025_rc1"
    actual, vistos = normalizar_cwe(cwe), set()
    while actual and actual not in vistos:
        vistos.add(actual)
        e = catalogo().get(actual)
        if not e:
            return ""
        valor = e.get(campo)
        if valor:
            return valor[0] if isinstance(valor, list) else valor
        if not heredar:
            return ""
        actual = e.get("padre", "")
    return ""


def cheatsheets_de(cwe) -> list[dict]:
    """Hojas de OWASP Cheat Sheet Series para un CWE (kb/cheatsheets.json).

    Si el CWE no tiene hoja propia, prueba con sus padres."""
    indice = _cargar("cheatsheets.json").get("por_cwe", {})
    hojas = _cargar("cheatsheets.json").get("hojas", {})
    actual, vistos = normalizar_cwe(cwe), set()
    while actual and actual not in vistos:
        vistos.add(actual)
        if actual in indice:
            return [{"nombre": n, "url": hojas[n]} for n in indice[actual] if n in hojas]
        actual = (catalogo().get(actual) or {}).get("padre", "")
    return []


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    for arg in argv:
        cwe = normalizar_cwe(arg)
        e = buscar_cwe(cwe)
        print(json.dumps({"cwe": cwe or arg, "existe": e is not None, **(e or {}),
                          "owasp": owasp_de(cwe), "cheatsheets": cheatsheets_de(cwe)},
                         ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
