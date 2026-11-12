#!/usr/bin/env python3
"""Descarga los hallazgos de SonarQube (API web) y los deja en JSON y en SARIF 2.1.0.

Lo invoca scripts/sonar-analizar.sh. El token se lee de la variable de entorno
SONAR_EXPORT_TOKEN (nunca por argumento). Genera en --salida:
    sonar-issues.json  sonar-hotspots.json  sonar-quality-gate.json  sonar.sarif
Sale con código 3 si hay hallazgos cuya severidad
está en --fail-on (así el pipeline bloquea aunque el servidor sea efímero y su quality
gate, que solo mira código nuevo, no tenga con qué comparar).
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# Severidad de SonarQube -> nivel SARIF
NIVEL = {
    "BLOCKER": "error",
    "CRITICAL": "error",
    "MAJOR": "warning",
    "MINOR": "note",
    "INFO": "note",
}


def _ruta(componente, clave_proyecto):
    """'proyecto:src/Archivo.cs' -> 'src/Archivo.cs'."""
    prefijo = clave_proyecto + ":"
    return componente[len(prefijo):] if componente.startswith(prefijo) else componente


def _get(host, ruta, parametros):
    """GET autenticado a la API web de SonarQube. Devuelve el JSON."""
    url = f"{host}{ruta}?{urllib.parse.urlencode(parametros)}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {os.environ.get('SONAR_EXPORT_TOKEN', '')}"})
    # El host viene de SONAR_HOST_URL (configuración del pipeline, no entrada de usuario)
    # y main() solo admite http(s).
    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host-url", required=True)
    ap.add_argument("--project-key", required=True)
    ap.add_argument("--fail-on", default="", help="Severidades que bloquean, separadas por coma")
    ap.add_argument("--salida", required=True, help="Carpeta de reportes")
    args = ap.parse_args()
    host = args.host_url.rstrip("/")
    if not host.lower().startswith(("http://", "https://")):
        sys.exit("ERROR: --host-url debe ser http(s)://")
    os.makedirs(args.salida, exist_ok=True)

    def ruta(nombre):
        return os.path.join(args.salida, nombre)

    issues, pagina = [], 1
    while True:
        doc = _get(host, "/api/issues/search", {
            "componentKeys": args.project_key, "resolved": "false", "ps": 500, "p": pagina})
        issues.extend(doc.get("issues", []))
        total = doc.get("paging", {}).get("total", doc.get("total", 0))
        if pagina * 500 >= total or not doc.get("issues"):
            break
        pagina += 1

    try:
        hotspots = _get(host, "/api/hotspots/search",
                        {"projectKey": args.project_key, "ps": 500}).get("hotspots", [])
    except urllib.error.URLError:
        hotspots = []
    with open(ruta("sonar-hotspots.json"), "w", encoding="utf-8") as f:
        json.dump({"hotspots": hotspots}, f, ensure_ascii=False, indent=2)

    try:
        gate = _get(host, "/api/qualitygates/project_status", {"projectKey": args.project_key})
        with open(ruta("sonar-quality-gate.json"), "w", encoding="utf-8") as f:
            json.dump(gate, f, ensure_ascii=False, indent=2)
        print(f">> Quality gate: {gate.get('projectStatus', {}).get('status', '?')}")
    except urllib.error.URLError:
        pass

    hallazgos = []
    for i in issues:
        hallazgos.append({
            "id": i.get("key", ""),
            "regla": i.get("rule", ""),
            "tipo": i.get("type", ""),
            "severidad": i.get("severity", "MAJOR"),
            "archivo": _ruta(i.get("component", ""), args.project_key),
            "linea": i.get("line", 0),
            "descripcion": i.get("message", ""),
        })
    for h in hotspots:
        hallazgos.append({
            "id": h.get("key", ""),
            "regla": h.get("ruleKey", h.get("securityCategory", "hotspot")),
            "tipo": "SECURITY_HOTSPOT",
            # Un hotspot es código a revisar, no un hallazgo confirmado: nunca bloquea.
            "severidad": "MAJOR",
            "archivo": _ruta(h.get("component", ""), args.project_key),
            "linea": h.get("line", 0),
            "descripcion": h.get("message", ""),
        })

    with open(ruta("sonar-issues.json"), "w", encoding="utf-8") as f:
        json.dump({"proyecto": args.project_key, "total": len(hallazgos),
                   "sin_hallazgos": not hallazgos, "hallazgos": hallazgos},
                  f, ensure_ascii=False, indent=2)

    reglas = sorted({h["regla"] for h in hallazgos})
    sarif = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "SonarQube Community",
                "informationUri": "https://www.sonarsource.com/products/sonarqube/",
                "rules": [{"id": r, "name": r} for r in reglas],
            }},
            "results": [{
                "ruleId": h["regla"],
                "level": NIVEL.get(h["severidad"], "warning"),
                "message": {"text": h["descripcion"]},
                "guid": h["id"],
                "properties": {"tipo": h["tipo"], "severidadSonar": h["severidad"]},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": h["archivo"]},
                    "region": {"startLine": max(int(h["linea"] or 1), 1)},
                }}],
            } for h in hallazgos],
        }],
    }
    with open(ruta("sonar.sarif"), "w", encoding="utf-8") as f:
        json.dump(sarif, f, ensure_ascii=False, indent=2)

    bloqueantes = {s.strip().upper() for s in args.fail_on.split(",") if s.strip()}
    malos = [h for h in hallazgos
             if h["tipo"] != "SECURITY_HOTSPOT" and h["severidad"] in bloqueantes]
    por_sev = {}
    for h in hallazgos:
        por_sev[h["severidad"]] = por_sev.get(h["severidad"], 0) + 1
    print(f">> SonarQube: {len(hallazgos)} hallazgo(s) {por_sev or ''} "
          f"({len(hotspots)} hotspot(s)); bloqueantes: {len(malos)}")
    for h in malos:
        print(f"   {h['severidad']} {h['regla']} {h['archivo']}:{h['linea']} {h['descripcion']}")
    sys.exit(3 if malos else 0)


if __name__ == "__main__":
    main()
