#!/usr/bin/env python3
"""Normaliza un reporte SARIF a un JSON común para los agentes del Grupo 7.

Uso:
    python3 scripts/normalizar_sarif.py reporte.sarif -o reportes/normalizado.json
    python3 scripts/normalizar_sarif.py objetivo.sarif --prefijo objetivos/mi-proyecto -o ...
    python3 scripts/normalizar_sarif.py dotnet/*.sarif --base /tmp/src --prefijo objetivos/p -o ...

--prefijo antepone una carpeta a las rutas relativas del SARIF (útil cuando el escáner
corrió dentro de la carpeta del proyecto y se quieren rutas relativas a la raíz del repo).

Soporta SARIF 2.1.0 (el formato que emiten Semgrep, Fortify y otros). Si el reporte
no tiene hallazgos, devuelve {"sin_hallazgos": true, "hallazgos": []}.

CWE y OWASP: se toman de las etiquetas de la regla y se normalizan a `CWE-<n>`. Si la
herramienta no trae OWASP (o trae solo el CWE, como los analizadores .NET `CAxxxx`), se
completa desde la base de conocimiento `agente-sast-g7/kb/cwe-owasp.json` (vista oficial
de MITRE OWASP Top Ten 2021). Sin la KB disponible, el campo queda como venga.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from kb import normalizar_cwe, owasp_de
except ImportError:  # el script se copió sin kb.py: se normaliza sin KB
    def normalizar_cwe(texto):
        m = re.search(r"CWE[\s_:\-]*(\d+)", str(texto or ""), re.IGNORECASE)
        return f"CWE-{int(m.group(1))}" if m else ""

    def owasp_de(cwe, version="2021", heredar=True):
        return ""

# Mapeo SARIF level -> (severidad, prioridad). Ver .github/copilot-instructions.md
NIVEL = {
    "error": ("Alta", "Alta"),
    "warning": ("Media", "Media"),
    "note": ("Baja", "Baja"),
    "none": ("Baja", "Baja"),
}


# Reglas de seguridad de los analizadores .NET (Microsoft.CodeAnalysis.NetAnalyzers), que
# no traen CWE en el SARIF. Fuente: documentación oficial de cada regla CAxxxx.
CWE_REGLAS_DOTNET = {
    "CA2100": "CWE-89", "CA3001": "CWE-89", "CA3002": "CWE-79", "CA3003": "CWE-22",
    "CA3004": "CWE-209", "CA3006": "CWE-78", "CA3007": "CWE-601", "CA3008": "CWE-643",
    "CA3009": "CWE-91", "CA3075": "CWE-611", "CA3077": "CWE-611", "CA3147": "CWE-352",
    "CA2300": "CWE-502", "CA2301": "CWE-502", "CA2302": "CWE-502", "CA2305": "CWE-502",
    "CA2310": "CWE-502", "CA2311": "CWE-502", "CA2312": "CWE-502", "CA2315": "CWE-502",
    "CA2321": "CWE-502", "CA2322": "CWE-502", "CA2326": "CWE-502", "CA2327": "CWE-502",
    "CA2328": "CWE-502", "CA2329": "CWE-502", "CA2330": "CWE-502",
    "CA5350": "CWE-327", "CA5351": "CWE-327", "CA5359": "CWE-295", "CA5364": "CWE-327",
    "CA5369": "CWE-611", "CA5370": "CWE-611", "CA5371": "CWE-611", "CA5372": "CWE-611",
    "CA5379": "CWE-916", "CA5385": "CWE-326", "CA5390": "CWE-321", "CA5394": "CWE-330",
    "CA5397": "CWE-327", "CA5403": "CWE-798",
}


def _indexar_reglas(run):
    """Devuelve {ruleId: {cwe, owasp, nombre}} a partir de las reglas del driver."""
    reglas = {}
    driver = run.get("tool", {}).get("driver", {})
    for regla in driver.get("rules", []):
        rid = regla.get("id", "")
        cwe, owasp = "", ""
        props = regla.get("properties", {})
        cwes = props.get("cwe", [])
        for tag in props.get("tags", []) + (cwes if isinstance(cwes, list) else [cwes]):
            t = str(tag)
            if not cwe and t.upper().startswith("CWE"):
                cwe = normalizar_cwe(t)
            if "OWASP" in t.upper() or re.match(r"A\d\d:\d{4}", t):
                # Semgrep etiqueta 2017 y 2021: se prefiere 2021, la versión de la KB.
                if not owasp or (":2021" in t and ":2021" not in owasp):
                    owasp = _owasp_etiqueta(t)
        cwe = cwe or CWE_REGLAS_DOTNET.get(rid, "")
        reglas[rid] = {"cwe": cwe, "owasp": owasp, "nombre": regla.get("name", rid)}
    return reglas


def _owasp_etiqueta(t):
    """'OWASP-A03:2021 - Injection' → 'A03:2021-Injection' (formato de la KB)."""
    m = re.search(r"(A\d\d:\d{4})\s*-?\s*(.*)", t)
    if not m:
        return t
    return f"{m.group(1)}-{m.group(2).strip()}" if m.group(2).strip() else m.group(1)


def _relativa(archivo, base):
    """file:///tmp/src/Controllers/X.cs con base=/tmp/src → Controllers/X.cs."""
    if archivo.startswith("file://"):
        archivo = unquote(archivo[len("file://"):])
    if base and archivo.startswith(base.rstrip("/") + "/"):
        archivo = archivo[len(base.rstrip("/")) + 1:]
    return archivo


def normalizar(sarif, prefijo="", base=""):
    hallazgos = []
    for run in sarif.get("runs", []):
        reglas = _indexar_reglas(run)
        for r in run.get("results", []):
            i = len(hallazgos)  # correlativo global: varios runs no repiten ids
            rid = r.get("ruleId", "")
            nivel = r.get("level", "warning")
            severidad, prioridad = NIVEL.get(nivel, ("Media", "Media"))
            loc = (r.get("locations") or [{}])[0]
            phys = loc.get("physicalLocation", {})
            archivo = phys.get("artifactLocation", {}).get("uri", "")
            linea = phys.get("region", {}).get("startLine", 0)
            archivo = _relativa(archivo, base)
            if prefijo and archivo and "://" not in archivo and not archivo.startswith("/"):
                archivo = prefijo.rstrip("/") + "/" + archivo.removeprefix("./")
            meta = reglas.get(rid, {})
            cwe = meta.get("cwe", "") or CWE_REGLAS_DOTNET.get(rid, "")
            owasp = meta.get("owasp", "") or owasp_de(cwe)
            hallazgos.append({
                "id": r.get("guid") or f"{rid}-{i}",
                "regla": rid,
                "severidad": severidad,
                "prioridad": prioridad,
                "cwe": cwe,
                "owasp": owasp,
                "archivo": archivo,
                "linea": linea,
                "descripcion": (r.get("message", {}) or {}).get("text", ""),
            })
    return {"sin_hallazgos": len(hallazgos) == 0, "total": len(hallazgos),
            "hallazgos": hallazgos}


def main():
    ap = argparse.ArgumentParser(description="Normaliza SARIF a JSON común del Grupo 7.")
    ap.add_argument("reporte", nargs="+", help="Ruta(s) al archivo .sarif (varios se unen en un solo JSON)")
    ap.add_argument("-o", "--salida", help="Archivo JSON de salida (si se omite, stdout)")
    ap.add_argument("--prefijo", default="", help="Carpeta a anteponer a las rutas relativas del SARIF")
    ap.add_argument("--base", default="",
                    help="Carpeta absoluta a quitar de las rutas file:// (p. ej. /tmp/src en los analizadores .NET)")
    args = ap.parse_args()

    runs = []
    for reporte in args.reporte:
        try:
            with open(reporte, encoding="utf-8-sig") as f:
                sarif = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"ERROR: no se pudo leer un SARIF válido ({reporte}): {e}", file=sys.stderr)
            sys.exit(2)
        if "runs" not in sarif:
            print(f"ERROR: {reporte} no parece SARIF (falta 'runs').", file=sys.stderr)
            sys.exit(2)
        runs += sarif["runs"]

    resultado = normalizar({"runs": runs}, args.prefijo, args.base)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write(texto)
        print(f">> {resultado['total']} hallazgo(s) normalizado(s) en {args.salida}")
    else:
        print(texto)


if __name__ == "__main__":
    main()
