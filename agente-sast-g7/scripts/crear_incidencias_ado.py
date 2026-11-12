#!/usr/bin/env python3
"""Crea work items en Azure DevOps por cada vulnerabilidad Crítica/Alta que sobrevivió
a la validación adversarial, sin duplicar.

Lee la configuración de variables de entorno (ver .env.example). El PAT NUNCA se pasa por
argumento ni se imprime: se lee de ADO_PAT.

Uso:
    python3 scripts/crear_incidencias_ado.py reportes/validado.json --dry-run
    python3 scripts/crear_incidencias_ado.py reportes/validado.json
    python3 scripts/crear_incidencias_ado.py --self-test
"""
import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse

API = "7.0"
PRIORIDADES_INCIDENCIA = {"Crítica", "Critica", "Alta"}


def _cargar_env():
    """Carga pares KEY=VALUE de un archivo .env si existe (sin dependencias externas)."""
    ruta = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith("#") and "=" in linea:
                    k, v = linea.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def _config():
    _cargar_env()
    cfg = {
        "org": os.environ.get("ADO_ORG_URL", "").rstrip("/"),
        "proyecto": os.environ.get("ADO_PROJECT", ""),
        "tipo": os.environ.get("ADO_WORKITEM_TYPE", "Bug"),
        "area": os.environ.get("ADO_AREA_PATH", ""),
        "iteracion": os.environ.get("ADO_ITERATION_PATH", ""),
        "pat": os.environ.get("ADO_PAT", ""),
    }
    if cfg["org"] and not cfg["org"].lower().startswith("https://"):
        print("ERROR: ADO_ORG_URL debe empezar por https://", file=sys.stderr)
        sys.exit(1)
    return cfg


def _headers(pat, content_type):
    token = base64.b64encode(f":{pat}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": content_type}


def _peticion(url, metodo, headers, cuerpo=None):
    data = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=metodo)
    # La URL se arma con ADO_ORG_URL/ADO_PROJECT (configuración del operador, no entrada
    # de usuario) y solo se admite https: ver _config().
    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def existe_incidencia(cfg, tag):
    """Evita duplicados: busca un work item con el tag del hallazgo (WIQL)."""
    url = f"{cfg['org']}/{cfg['proyecto']}/_apis/wit/wiql?api-version={API}"
    wiql = {"query": "SELECT [System.Id] FROM WorkItems WHERE "
                     f"[System.TeamProject] = '{cfg['proyecto']}' "
                     f"AND [System.Tags] CONTAINS '{tag}'"}
    try:
        r = _peticion(url, "POST", _headers(cfg["pat"], "application/json"), wiql)
        return len(r.get("workItems", [])) > 0
    except urllib.error.URLError:
        return False


def crear_incidencia(cfg, h):
    tag = f"sast-{h['id']}"
    titulo = f"[SAST] {h.get('regla','')} — {h.get('archivo','')}:{h.get('linea','')}"
    descripcion = (
        f"<b>Severidad:</b> {h.get('severidad')}<br>"
        f"<b>CWE:</b> {h.get('cwe','N/A')} &nbsp; <b>OWASP:</b> {h.get('owasp','N/A')}<br>"
        f"<b>Ubicación:</b> {h.get('archivo')}:{h.get('linea')}<br>"
        f"<b>Descripción:</b> {h.get('descripcion','')}<br>"
        f"<b>Recomendación:</b> {h.get('recomendacion','(ver reporte)')}"
    )
    campos = [
        {"op": "add", "path": "/fields/System.Title", "value": titulo[:255]},
        {"op": "add", "path": "/fields/System.Description", "value": descripcion},
        {"op": "add", "path": "/fields/System.Tags", "value": f"{tag}; SAST; Grupo7"},
    ]
    if cfg["area"]:
        campos.append({"op": "add", "path": "/fields/System.AreaPath", "value": cfg["area"]})
    if cfg["iteracion"]:
        campos.append({"op": "add", "path": "/fields/System.IterationPath",
                       "value": cfg["iteracion"]})
    tipo = urllib.parse.quote(f"${cfg['tipo']}")
    url = f"{cfg['org']}/{cfg['proyecto']}/_apis/wit/workitems/{tipo}?api-version={API}"
    r = _peticion(url, "POST", _headers(cfg["pat"], "application/json-patch+json"), campos)
    return r.get("id")


def self_test():
    cfg = _config()
    faltan = [k for k in ("org", "proyecto", "pat") if not cfg[k]]
    if faltan:
        print(f"FALTAN variables: {', '.join(faltan)}. Revisa .env / docs/ADO-CREDENCIALES.md")
        sys.exit(1)
    url = f"{cfg['org']}/{cfg['proyecto']}/_apis/wit/fields?api-version={API}"
    try:
        _peticion(url, "GET", _headers(cfg["pat"], "application/json"))
        print(f"OK: conexión válida a {cfg['org']}/{cfg['proyecto']} (PAT no mostrado).")
    except urllib.error.HTTPError as e:
        print(f"ERROR {e.code}: revisa org/proyecto/permiso del PAT (Work Items R/W).")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="Crea incidencias SAST en Azure DevOps.")
    ap.add_argument("validado", nargs="?", help="JSON con hallazgos validados")
    ap.add_argument("--dry-run", action="store_true", help="Previsualiza sin crear nada")
    ap.add_argument("--self-test", action="store_true", help="Prueba la conexión y sale")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    if not args.validado:
        ap.error("falta el archivo de hallazgos validados (o usa --self-test)")

    cfg = _config()
    with open(args.validado, encoding="utf-8") as f:
        datos = json.load(f)

    candidatos = [h for h in datos.get("hallazgos", [])
                  if h.get("veredicto", "sobrevive") == "sobrevive"
                  and h.get("prioridad") in PRIORIDADES_INCIDENCIA]
    print(f">> {len(candidatos)} candidato(s) Crítica/Alta que sobrevivieron.")

    for h in candidatos:
        if args.dry_run:
            print(f"   [dry-run] crearía: [SAST] {h.get('regla')} — "
                  f"{h.get('archivo')}:{h.get('linea')}")
            continue
        if not all((cfg["org"], cfg["proyecto"], cfg["pat"])):
            print("ERROR: faltan credenciales. Ver docs/ADO-CREDENCIALES.md", file=sys.stderr)
            sys.exit(1)
        if existe_incidencia(cfg, f"sast-{h['id']}"):
            print(f"   = ya existe incidencia para {h['id']}, se omite.")
            continue
        wid = crear_incidencia(cfg, h)
        print(f"   + work item #{wid} creado para {h['id']}.")


if __name__ == "__main__":
    main()
