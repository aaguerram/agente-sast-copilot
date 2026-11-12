#!/usr/bin/env python3
"""Genera la base de conocimiento CWE → OWASP (agente-sast-g7/kb/cwe-owasp.json).

Fuente: catálogo oficial de MITRE CWE (https://cwe.mitre.org/data/downloads.html).
El mapeo a OWASP sale de las vistas oficiales de MITRE:
    CWE-1344  "Weaknesses in OWASP Top Ten (2021)"
    CWE-1450  "Weaknesses in OWASP Top Ten RC1 (2025)"   (si existe en el XML)

Uso (solo Docker, nunca instales nada):
    docker compose --profile agentes run --rm py agente-sast-g7/scripts/kb_cwe.py
    docker compose --profile agentes run --rm py agente-sast-g7/scripts/kb_cwe.py --xml salida/kb/cwec_latest.xml.zip

El JSON resultante se versiona: los agentes y los scripts lo usan sin red (offline).
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

URL = "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip"
SALIDA = Path(__file__).resolve().parents[1] / "kb" / "cwe-owasp.json"
VISTAS = {"owasp_2021": "1344", "owasp_2025_rc1": "1450"}
NOMBRE_OWASP = re.compile(r"Category (A\d\d:\d{4}) - (.+)$")
CIA = {"Confidentiality": "C", "Integrity": "I", "Availability": "D"}


def _sin_ns(elem: ET.Element) -> None:
    for e in elem.iter():
        if "}" in e.tag:
            e.tag = e.tag.split("}", 1)[1]


def cargar_xml(origen: str | None) -> tuple[ET.Element, str]:
    if origen:
        datos = Path(origen).read_bytes()
        fuente = Path(origen).name
    else:
        print(f">> descargando {URL}", file=sys.stderr)
        # URL fija y oficial (constante https del módulo), no entra del usuario.
        # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
        with urllib.request.urlopen(URL, timeout=120) as r:  # noqa: S310
            datos = r.read()
        fuente = URL
    if datos[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(datos))
        datos = z.read(z.namelist()[0])
    raiz = ET.fromstring(datos)
    _sin_ns(raiz)
    return raiz, fuente


def construir(raiz: ET.Element, fuente: str) -> dict:
    # Grupos (CWE 5.x los llama Grouping; versiones anteriores, Category).
    grupos = {g.get("ID"): g for g in list(raiz.iter("Grouping")) + list(raiz.iter("Category"))}
    vistas = {v.get("ID"): v for v in raiz.iter("View")}

    pertenencia: dict[str, dict[str, list[str]]] = {}
    vistas_usadas = {}
    for campo, vid in VISTAS.items():
        vista = vistas.get(vid)
        if vista is None:
            continue
        vistas_usadas[campo] = {"id": f"CWE-{vid}", "nombre": vista.get("Name")}
        for m in vista.iter("Has_Member"):
            g = grupos.get(m.get("CWE_ID"))
            if g is None:
                continue
            nm = NOMBRE_OWASP.search(g.get("Name", ""))
            if not nm:
                continue
            etiqueta = f"{nm.group(1)}-{nm.group(2).strip()}"
            for miembro in g.iter("Has_Member"):
                lista = pertenencia.setdefault(miembro.get("CWE_ID"), {}).setdefault(campo, [])
                if etiqueta not in lista:
                    lista.append(etiqueta)

    cwes = {}
    for w in raiz.iter("Weakness"):
        if w.get("Status") == "Deprecated":
            continue
        wid = w.get("ID")
        e: dict = {"nombre": w.get("Name"), "abstraccion": w.get("Abstraction")}
        uso = w.find("Mapping_Notes/Usage")
        if uso is not None and uso.text:
            e["uso"] = uso.text.strip()
        lik = w.find("Likelihood_Of_Exploit")
        if lik is not None and lik.text:
            e["probabilidad"] = lik.text.strip()
        imp = sorted({CIA[s.text.strip()] for s in w.iter("Scope") if s.text and s.text.strip() in CIA},
                     key="CID".index)
        if imp:
            e["impacto"] = "".join(imp)
        padre = next((r.get("CWE_ID") for r in w.iter("Related_Weakness")
                      if r.get("Nature") == "ChildOf" and r.get("View_ID") == "1000"
                      and r.get("Ordinal") == "Primary"), None)
        if padre:
            e["padre"] = f"CWE-{padre}"
        for campo, lista in pertenencia.get(wid, {}).items():
            e[campo] = lista[0] if len(lista) == 1 else lista
        cwes[f"CWE-{wid}"] = e

    # Agrupaciones (antes "categorías", p. ej. CWE-840 Business Logic Errors): MITRE
    # desaconseja o prohíbe usarlas para mapear, pero algunas están en la vista OWASP.
    for gid, g in grupos.items():
        if g.get("Status") == "Deprecated" or f"CWE-{gid}" in cwes:
            continue
        e = {"nombre": g.get("Name"), "abstraccion": "Grouping"}
        uso = g.find("Mapping_Notes/Usage")
        if uso is not None and uso.text:
            e["uso"] = uso.text.strip()
        for campo, lista in pertenencia.get(gid, {}).items():
            e[campo] = lista[0] if len(lista) == 1 else lista
        cwes[f"CWE-{gid}"] = e

    return {
        "descripcion": "Base de conocimiento CWE → OWASP generada desde el catálogo oficial de MITRE. "
                       "owasp_* sale de las vistas oficiales de MITRE; impacto: C=confidencialidad, "
                       "I=integridad, D=disponibilidad; uso = Mapping Notes (Allowed, "
                       "Allowed-with-Review, Discouraged, Prohibited).",
        "fuente": fuente,
        "version_cwe": raiz.get("Version"),
        "fecha_cwe": raiz.get("Date"),
        "vistas": vistas_usadas,
        "licencia": "CWE™ © The MITRE Corporation; uso según https://cwe.mitre.org/about/termsofuse.html",
        "total": len(cwes),
        "total_debilidades": sum(1 for e in cwes.values() if e["abstraccion"] != "Grouping"),
        "cwe": dict(sorted(cwes.items(), key=lambda kv: int(kv[0][4:]))),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml", help="zip o XML local de MITRE (si no, se descarga)")
    ap.add_argument("-o", "--salida", default=str(SALIDA))
    args = ap.parse_args(argv)
    raiz, fuente = cargar_xml(args.xml)
    if args.xml:
        fuente = f"{URL} ({fuente})"
    kb = construir(raiz, fuente)
    destino = Path(args.salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(kb, ensure_ascii=False, separators=(",", ":"))
    # Una línea por CWE: compacto y con diffs legibles.
    texto = texto.replace(',"CWE-', ',\n"CWE-').replace('"cwe":{"CWE-', '"cwe":{\n"CWE-')
    destino.write_text(texto + "\n", encoding="utf-8")
    con = sum(1 for e in kb["cwe"].values() if "owasp_2021" in e)
    print(f">> {kb['total']} entradas (v{kb['version_cwe']}), {con} con OWASP 2021 → {destino}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
