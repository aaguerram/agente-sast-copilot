#!/usr/bin/env bash
# Ejecuta, sigue y descarga el pipeline de seguridad de Azure DevOps por la API REST.
# No depende de la extensión "az pipelines" (en algunas organizaciones no autentica con
# la sesión de az login): usa el token de Entra ID de "az login" o un PAT.
#
#   ./scripts/ado-pipeline.sh --org https://dev.azure.com/ORG --project PROY <subcomando>
#   ./scripts/ado.sh ./scripts/ado-pipeline.sh ...      # mismo script, con az en contenedor
#
# Subcomandos:
#   ejecutar [--rama main] --si        Encola el pipeline (consume minutos: exige --si).
#   seguir <buildId>                   Espera a que termine y muestra el resultado por job.
#   seguir --pr <n> | --rama <rama>    Igual, sobre el último build del PR o de la rama.
#   descargar <buildId> [--artefacto CodeAnalysisLogs] [--dir salida/reportes/pipeline-<id>]
#   estado-pr <n>                      Estado del PR, mergeStatus y su último build.
#
# Opciones comunes (o variables de entorno):
#   --org URL       (ADO_ORG_URL)    https://dev.azure.com/ORG
#   --project NOM   (ADO_PROJECT)
#   --repo NOM      (ADO_REPO)       def. nombre de la carpeta del repo
#   --pipeline NOM  (ADO_PIPELINE)   def. <repo>-seguridad
#   --intervalo S   (def. 30)  y  --timeout S (def. 3600) para "seguir"
#
# Códigos de salida de "seguir": 0 succeeded, 1 otro resultado, 2 timeout.
# Autenticación: AZURE_DEVOPS_EXT_PAT si está definido (solo en el entorno, nunca en un
# archivo); si no, la sesión de "az login". El token nunca se escribe en disco.
#
# Ejemplos:
#   ./scripts/ado-pipeline.sh --org https://dev.azure.com/ORG --project PROY seguir --pr 30
#   ./scripts/ado-pipeline.sh --org ... --project ... ejecutar --rama main --si
#   ./scripts/ado-pipeline.sh --org ... --project ... descargar 55
set -euo pipefail

ADO_RESOURCE="499b84ac-1321-427f-aa17-267ca6975798"   # id público de Azure DevOps en Entra ID
uso() { sed -n '2,31p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

ORG="${ADO_ORG_URL:-}"; PROJECT="${ADO_PROJECT:-}"
REPO="${ADO_REPO:-}"; PIPELINE="${ADO_PIPELINE:-}"
INTERVALO=30; TIMEOUT=3600
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --org) ORG="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --pipeline) PIPELINE="$2"; shift 2 ;;
    --intervalo) INTERVALO="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    -h|--help) uso 0 ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
[ "${#ARGS[@]}" -gt 0 ] || uso 1
ORG="${ORG%/}"
[ -n "$ORG" ] && [ -n "$PROJECT" ] || { echo "ERROR: faltan --org y --project (o ADO_ORG_URL / ADO_PROJECT)." >&2; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: falta python3." >&2; exit 1; }
if [ -z "$REPO" ]; then
  REPO="$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")"
fi
PIPELINE="${PIPELINE:-$REPO-seguridad}"

# Cabecera de autenticación: solo en memoria y en el entorno del proceso python.
if [ -n "${AZURE_DEVOPS_EXT_PAT:-}" ]; then
  ADO_AUTH="Basic $(printf ':%s' "$AZURE_DEVOPS_EXT_PAT" | base64 | tr -d '\n')"
elif command -v az >/dev/null; then
  TOKEN="$(az account get-access-token --resource "$ADO_RESOURCE" --query accessToken -o tsv 2>/dev/null)" ||
    { echo "ERROR: no hay sesión de Azure CLI. Ejecuta: ./scripts/ado.sh az login --use-device-code" >&2; exit 1; }
  ADO_AUTH="Bearer $TOKEN"; unset TOKEN
else
  echo "ERROR: define AZURE_DEVOPS_EXT_PAT o usa Azure CLI: ./scripts/ado.sh az login --use-device-code" >&2
  exit 1
fi

ADO_AUTH="$ADO_AUTH" ORG="$ORG" PROJECT="$PROJECT" REPO="$REPO" PIPELINE="$PIPELINE" \
INTERVALO="$INTERVALO" TIMEOUT="$TIMEOUT" exec python3 - "${ARGS[@]}" <<'PY'
import io, json, os, sys, time, urllib.error, urllib.parse, urllib.request, zipfile

ORG, PROJECT, REPO, PIPELINE = (os.environ[k] for k in ("ORG", "PROJECT", "REPO", "PIPELINE"))
AUTH = os.environ.pop("ADO_AUTH")
INTERVALO, TIMEOUT = int(os.environ["INTERVALO"]), int(os.environ["TIMEOUT"])
BASE = f"{ORG}/{urllib.parse.quote(PROJECT)}/_apis"
API = "7.1"


class SinAuthEnRedireccion(urllib.request.HTTPRedirectHandler):
    """Al redirigir a otro host (p. ej. blob storage) no reenvía la cabecera Authorization."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        nuevo = super().redirect_request(req, fp, code, msg, headers, newurl)
        if nuevo and urllib.parse.urlsplit(newurl).netloc != urllib.parse.urlsplit(req.full_url).netloc:
            nuevo.headers.pop("Authorization", None)
            nuevo.unredirected_hdrs.pop("Authorization", None)
        return nuevo


HTTP = urllib.request.build_opener(SinAuthEnRedireccion)


def fallar(msg, codigo=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(codigo)


def peticion(url, metodo="GET", cuerpo=None, crudo=False, params=None):
    params = dict(params or {})
    params.setdefault("api-version", API)
    url = f"{url}{'&' if '?' in url else '?'}{urllib.parse.urlencode(params)}"
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(url, data=datos, method=metodo,
                                 headers={"Authorization": AUTH, "Accept": "application/json",
                                          "Content-Type": "application/json"})
    try:
        with HTTP.open(req, timeout=120) as r:
            contenido = r.read()
    except urllib.error.HTTPError as e:
        detalle = e.read().decode(errors="replace")
        try:
            detalle = json.loads(detalle).get("message", detalle)
        except ValueError:
            detalle = detalle[:200]
        fallar(f"{metodo} {url.split('?')[0]} → HTTP {e.code}: {detalle}")
    except urllib.error.URLError as e:
        fallar(f"{metodo} {url.split('?')[0]} → {e.reason}")
    if crudo:
        return contenido
    if contenido.lstrip()[:1] == b"<":   # página HTML de login: credenciales no válidas
        fallar("Azure DevOps devolvió HTML en vez de JSON: revisa el login o el PAT y la organización.")
    return json.loads(contenido) if contenido else {}


def id_pipeline():
    for p in peticion(f"{BASE}/pipelines").get("value", []):
        if p["name"] == PIPELINE:
            return p["id"]
    fallar(f"no existe el pipeline '{PIPELINE}' en {ORG}/{PROJECT} (usa --pipeline).")


def ultimo_build(rama):
    builds = peticion(f"{BASE}/build/builds", params={
        "definitions": id_pipeline(), "branchName": rama,
        "queryOrder": "queueTimeDescending", "$top": 1}).get("value", [])
    if not builds:
        fallar(f"no hay builds de '{PIPELINE}' para {rama}.")
    return builds[0]


def build(bid):
    return peticion(f"{BASE}/build/builds/{int(bid)}")


def jobs(bid):
    registros = peticion(f"{BASE}/build/builds/{int(bid)}/timeline").get("records", [])
    return sorted((r for r in registros if r.get("type") == "Job"), key=lambda r: r.get("order") or 0)


def url_web(b):
    return b.get("_links", {}).get("web", {}).get("href", "")


def opcion(args, nombre, defecto=None):
    if nombre in args:
        i = args.index(nombre)
        if i + 1 >= len(args):
            fallar(f"falta el valor de {nombre}")
        valor = args[i + 1]
        del args[i:i + 2]
        return valor
    return defecto


def resolver_build(args):
    pr, rama = opcion(args, "--pr"), opcion(args, "--rama")
    if pr:
        return ultimo_build(f"refs/pull/{int(pr)}/merge")
    if rama:
        return ultimo_build(rama if rama.startswith("refs/") else f"refs/heads/{rama}")
    if not args:
        fallar("indica <buildId>, --pr <n> o --rama <rama>.")
    return build(args[0])


def cmd_ejecutar(args):
    rama = opcion(args, "--rama", "main")
    if "--si" not in args:
        fallar(f"encolar '{PIPELINE}' en {rama} consume minutos del agente: repite con --si.")
    ref = rama if rama.startswith("refs/") else f"refs/heads/{rama}"
    run = peticion(f"{BASE}/pipelines/{id_pipeline()}/runs", "POST",
                   {"resources": {"repositories": {"self": {"refName": ref}}}})
    print(f"Encolado: build {run['id']} ({run.get('state')}) {run.get('_links', {}).get('web', {}).get('href', '')}")
    print(run["id"])


def cmd_seguir(args):
    b = resolver_build(args)
    bid, inicio, anterior = b["id"], time.time(), None
    print(f"Build {bid} · {b.get('sourceBranch')} · {url_web(b)}", flush=True)
    while b.get("status") != "completed":
        if time.time() - inicio > TIMEOUT:
            print(f"TIMEOUT tras {TIMEOUT}s: el build {bid} sigue '{b.get('status')}'.")
            sys.exit(2)
        if b.get("status") != anterior:
            anterior = b.get("status")
            print(f"  {time.strftime('%H:%M:%S')} estado: {anterior}", flush=True)
            if anterior == "notStarted":
                print("  (si no arranca, puede faltar paralelismo hospedado: https://aka.ms/azpipelines-parallelism-request)")
        time.sleep(INTERVALO)
        b = build(bid)
    resultado = b.get("result")
    print(f"\nBuild {bid}: {resultado}\n")
    filas = [(j.get("name", "?"), j.get("result") or j.get("state") or "?") for j in jobs(bid)]
    ancho = max([len("Job")] + [len(n) for n, _ in filas])
    print(f"{'Job'.ljust(ancho)}  Resultado")
    for nombre, res in filas:
        print(f"{nombre.ljust(ancho)}  {res}")
    sys.exit(0 if resultado == "succeeded" else 1)


def cmd_descargar(args):
    artefacto = opcion(args, "--artefacto", "CodeAnalysisLogs")
    destino = opcion(args, "--dir")
    if not args:
        fallar("indica <buildId>.")
    bid = int(args[0])
    destino = destino or os.path.join("salida", "reportes", f"pipeline-{bid}")
    info = peticion(f"{BASE}/build/builds/{bid}/artifacts", params={"artifactName": artefacto})
    url = info.get("resource", {}).get("downloadUrl")
    if not url:
        fallar(f"el build {bid} no tiene el artefacto '{artefacto}'.")
    contenido = peticion(url, crudo=True)
    os.makedirs(destino, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(contenido)) as z:
        for nombre in z.namelist():   # sin rutas absolutas ni "..": nada fuera del destino
            ruta = os.path.normpath(os.path.join(destino, nombre))
            if not ruta.startswith(os.path.normpath(destino) + os.sep):
                fallar(f"ruta no permitida en el zip: {nombre}")
        z.extractall(destino)
        archivos = [n for n in z.namelist() if not n.endswith("/")]
    print(f"Artefacto '{artefacto}' del build {bid} → {destino}")
    for n in archivos:
        print(f"  {n}")


def cmd_estado_pr(args):
    if not args:
        fallar("indica el número de PR.")
    n = int(args[0])
    pr = peticion(f"{BASE}/git/repositories/{urllib.parse.quote(REPO)}/pullrequests/{n}")
    print(f"PR {n}: {pr.get('title')}")
    print(f"  estado:       {pr.get('status')}")
    print(f"  mergeStatus:  {pr.get('mergeStatus')}")
    print(f"  rama:         {pr.get('sourceRefName')} → {pr.get('targetRefName')}")
    builds = peticion(f"{BASE}/build/builds", params={
        "definitions": id_pipeline(), "branchName": f"refs/pull/{n}/merge",
        "queryOrder": "queueTimeDescending", "$top": 1}).get("value", [])
    if builds:
        b = builds[0]
        print(f"  último build: {b['id']} · {b.get('status')} · {b.get('result') or '-'} · {url_web(b)}")
    else:
        print("  último build: ninguno")


COMANDOS = {"ejecutar": cmd_ejecutar, "seguir": cmd_seguir,
            "descargar": cmd_descargar, "estado-pr": cmd_estado_pr}
args = sys.argv[1:]
if args[0] not in COMANDOS:
    fallar(f"subcomando desconocido '{args[0]}'. Usa: {', '.join(COMANDOS)} (o --help).")
COMANDOS[args[0]](args[1:])
PY
