#!/usr/bin/env python3
"""Normaliza un reporte SARIF a un JSON común para los agentes del Grupo 7.

Uso:
    python3 scripts/normalizar_sarif.py reporte.sarif -o reportes/normalizado.json
    python3 scripts/normalizar_sarif.py objetivo.sarif --prefijo objetivos/mi-proyecto -o ...

--prefijo antepone una carpeta a las rutas relativas del SARIF (útil cuando el escáner
corrió dentro de la carpeta del proyecto y se quieren rutas relativas a la raíz del repo).

Soporta SARIF 2.1.0 (el formato que emiten Semgrep, Fortify y otros). Si el reporte
no tiene hallazgos, devuelve {"sin_hallazgos": true, "hallazgos": []}.
"""
import argparse
import json
import sys

# Mapeo SARIF level -> (severidad, prioridad). Ver .github/copilot-instructions.md
NIVEL = {
    "error": ("Alta", "Alta"),
    "warning": ("Media", "Media"),
    "note": ("Baja", "Baja"),
    "none": ("Baja", "Baja"),
}


def _indexar_reglas(run):
    """Devuelve {ruleId: {cwe, owasp, nombre}} a partir de las reglas del driver."""
    reglas = {}
    driver = run.get("tool", {}).get("driver", {})
    for regla in driver.get("rules", []):
        rid = regla.get("id", "")
        cwe, owasp = "", ""
        props = regla.get("properties", {})
        for tag in props.get("tags", []) + props.get("cwe", []):
            t = str(tag)
            if t.upper().startswith("CWE"):
                cwe = t.upper().replace("CWE_", "CWE-").replace("CWE:", "CWE-")
            if "OWASP" in t.upper() or t.upper().startswith("A0"):
                owasp = t
        reglas[rid] = {"cwe": cwe, "owasp": owasp, "nombre": regla.get("name", rid)}
    return reglas


def normalizar(sarif, prefijo=""):
    hallazgos = []
    for run in sarif.get("runs", []):
        reglas = _indexar_reglas(run)
        for i, r in enumerate(run.get("results", [])):
            rid = r.get("ruleId", "")
            nivel = r.get("level", "warning")
            severidad, prioridad = NIVEL.get(nivel, ("Media", "Media"))
            loc = (r.get("locations") or [{}])[0]
            phys = loc.get("physicalLocation", {})
            archivo = phys.get("artifactLocation", {}).get("uri", "")
            linea = phys.get("region", {}).get("startLine", 0)
            if prefijo and archivo and "://" not in archivo and not archivo.startswith("/"):
                archivo = prefijo.rstrip("/") + "/" + archivo.removeprefix("./")
            meta = reglas.get(rid, {})
            hallazgos.append({
                "id": r.get("guid") or f"{rid}-{i}",
                "regla": rid,
                "severidad": severidad,
                "prioridad": prioridad,
                "cwe": meta.get("cwe", ""),
                "owasp": meta.get("owasp", ""),
                "archivo": archivo,
                "linea": linea,
                "descripcion": (r.get("message", {}) or {}).get("text", ""),
            })
    return {"sin_hallazgos": len(hallazgos) == 0, "total": len(hallazgos),
            "hallazgos": hallazgos}


def main():
    ap = argparse.ArgumentParser(description="Normaliza SARIF a JSON común del Grupo 7.")
    ap.add_argument("reporte", help="Ruta al archivo .sarif")
    ap.add_argument("-o", "--salida", help="Archivo JSON de salida (si se omite, stdout)")
    ap.add_argument("--prefijo", default="", help="Carpeta a anteponer a las rutas relativas del SARIF")
    args = ap.parse_args()

    try:
        with open(args.reporte, encoding="utf-8") as f:
            sarif = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: no se pudo leer un SARIF válido: {e}", file=sys.stderr)
        sys.exit(2)

    if "runs" not in sarif:
        print("ERROR: el archivo no parece SARIF (falta 'runs').", file=sys.stderr)
        sys.exit(2)

    resultado = normalizar(sarif, args.prefijo)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write(texto)
        print(f">> {resultado['total']} hallazgo(s) normalizado(s) en {args.salida}")
    else:
        print(texto)


if __name__ == "__main__":
    main()
