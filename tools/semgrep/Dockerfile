# Semgrep CE con las reglas del registro (p/default, p/csharp, p/secrets) YA descargadas:
# los escaneos no necesitan internet y no bajan las reglas en cada ejecución.
# Se guardan como JSON en la raíz (/p-*.json): así Semgrep las carga más rápido que el YAML
# y los ruleId quedan idénticos a los del registro (una carpeta añadiría su nombre como prefijo).
# Para actualizar las reglas: docker compose --profile seguridad build --no-cache semgrep
ARG SEMGREP_VERSION=1.185.0
FROM semgrep/semgrep:${SEMGREP_VERSION}
ARG SEMGREP_VERSION
RUN python3 - <<'PY'
import json, os, urllib.request
from ruamel.yaml import YAML

for paquete in ("default", "csharp", "secrets"):
    req = urllib.request.Request(f"https://semgrep.dev/c/p/{paquete}",
                                 headers={"User-Agent": f"Semgrep/{os.environ.get('SEMGREP_VERSION', '')}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        reglas = YAML(typ="safe").load(resp.read().decode("utf-8"))
    assert reglas["rules"], f"p/{paquete} llegó vacío"
    with open(f"/p-{paquete}.json", "w", encoding="utf-8") as f:
        json.dump(reglas, f, default=str)
    print(f"p/{paquete}: {len(reglas['rules'])} reglas")
PY
ENV SEMGREP_SEND_METRICS=off \
    SEMGREP_ENABLE_VERSION_CHECK=0
