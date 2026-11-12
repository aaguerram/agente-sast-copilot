#!/usr/bin/env python3
"""Genera los requisitos por defecto del paso 5 (agente-sast-g7/kb/asvs-requisitos.md)
desde OWASP ASVS (https://github.com/OWASP/ASVS), licencia CC BY-SA 4.0.

Se usa cuando el proyecto objetivo no trae su propio REQUISITOS.md: el analizador de gaps
compara el código con estos controles verificables en lugar de omitir el paso.

Subconjunto: capítulos aplicables a una API/web .NET de banca, niveles L1 y L2 (L3 queda
fuera por ser para aplicaciones de máxima criticidad y alargar el análisis).

    docker compose --profile agentes run --rm py agente-sast-g7/scripts/kb_asvs.py
    docker compose --profile agentes run --rm py agente-sast-g7/scripts/kb_asvs.py --json salida/kb/asvs5.flat.json
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

VERSION = "5.0.0"
URL = ("https://github.com/OWASP/ASVS/releases/download/v5.0.0_release/"
       "OWASP_Application_Security_Verification_Standard_5.0.0_en.flat.json")
SALIDA = Path(__file__).resolve().parents[1] / "kb" / "asvs-requisitos.md"

# capítulo → (nombre en español, CWE típicos para tipificar el gap, niveles incluidos)
CAPITULOS = {
    "V8": ("Autorización (incluye IDOR)", "CWE-862, CWE-863, CWE-639", {"1", "2"}),
    "V6": ("Autenticación", "CWE-287, CWE-306, CWE-307, CWE-798", {"1", "2"}),
    "V7": ("Gestión de sesión", "CWE-384, CWE-614, CWE-1004", {"1", "2"}),
    "V9": ("Tokens autocontenidos (JWT)", "CWE-347, CWE-345", {"1", "2"}),
    "V2": ("Validación y lógica de negocio", "CWE-20, CWE-840, CWE-841", {"1", "2"}),
    "V1": ("Codificación y saneamiento (inyección)", "CWE-89, CWE-78, CWE-79, CWE-74", {"1", "2"}),
    "V4": ("API y servicios web", "CWE-16, CWE-942", {"1", "2"}),
    "V5": ("Manejo de archivos", "CWE-22, CWE-434", {"1", "2"}),
    "V15": ("Código y arquitectura seguros", "CWE-502, CWE-915, CWE-1104", {"1", "2"}),
    "V11": ("Criptografía", "CWE-327, CWE-328, CWE-330", {"1", "2"}),
    "V12": ("Comunicación segura", "CWE-319, CWE-295", {"1"}),
    "V13": ("Configuración", "CWE-16, CWE-798, CWE-209", {"1", "2"}),
    "V14": ("Protección de datos", "CWE-200, CWE-312, CWE-532", {"1", "2"}),
    "V16": ("Registro de seguridad y manejo de errores", "CWE-778, CWE-117, CWE-209", {"1", "2"}),
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", help="flat.json local del release de ASVS (si no, se descarga)")
    ap.add_argument("-o", "--salida", default=str(SALIDA))
    args = ap.parse_args(argv)
    if args.json:
        datos = json.loads(Path(args.json).read_text(encoding="utf-8"))
    else:
        print(f">> descargando {URL}", file=sys.stderr)
        # URL fija y oficial (constante https del módulo), no entra del usuario.
        # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
        with urllib.request.urlopen(URL, timeout=120) as r:  # noqa: S310
            datos = json.loads(r.read())
    reqs = datos["requirements"] if isinstance(datos, dict) else datos

    lineas = [
        f"# Requisitos por defecto — OWASP ASVS {VERSION} (subconjunto L1/L2)",
        "",
        "> Generado por `agente-sast-g7/scripts/kb_asvs.py`; no editar a mano.",
        f"> Fuente: OWASP Application Security Verification Standard {VERSION},",
        "> https://github.com/OWASP/ASVS — © OWASP Foundation, licencia",
        "> [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Texto original en inglés.",
        "",
        "**Uso (paso 5, `analizador-gaps`):** si el proyecto objetivo no trae `REQUISITOS.md`,",
        "cada control de esta lista es un requisito verificable. El ID del gap es el del control",
        "(`requisito: \"ASVS-V8.2.2\"`) y `requisitos_fuente` apunta a este archivo. Revisa",
        "primero L1 y luego L2; un control que no aplica al proyecto (p. ej. no hay subida de",
        "archivos) se registra en `cumplidos` con `\"evidencia\": \"no aplica: …\"`.",
        "",
    ]
    total = 0
    for cap, (nombre, cwes, niveles) in CAPITULOS.items():
        del_cap = [r for r in reqs if r["chapter_id"] == cap and str(r["L"]) in niveles]
        if not del_cap:
            continue
        en = del_cap[0]["chapter_name"]
        lineas += [f"## {cap} — {nombre} ({en})", "", f"CWE típicos del gap: {cwes}.", ""]
        seccion = None
        for r in del_cap:
            if r["section_id"] != seccion:
                seccion = r["section_id"]
                if lineas[-1]:
                    lineas.append("")
                lineas += [f"### {seccion} {r['section_name']}", ""]
            texto = " ".join(r["req_description"].split())
            lineas.append(f"- **ASVS-{r['req_id']}** (L{r['L']}) {texto}")
            total += 1
        lineas.append("")
    lineas.insert(2, f"Total: {total} controles.\n")
    destino = Path(args.salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(lineas).rstrip() + "\n", encoding="utf-8")
    print(f">> {total} controles ASVS {VERSION} → {destino}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
