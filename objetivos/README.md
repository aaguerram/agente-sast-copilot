# objetivos/ — proyectos reales a analizar

Aquí se clonan los **proyectos del concurso con vulnerabilidades reales** sobre los que se
ejecutan los agentes de Copilot. Todo lo que pongas en esta carpeta (salvo este README):

- **no se versiona** (`.gitignore`: `objetivos/*`),
- **no entra a los controles bloqueantes** del repo: pre-commit, gitleaks, Semgrep
  bloqueante y SonarQube lo excluyen, así un proyecto vulnerable no rompe el pipeline.

```bash
git clone <url-del-proyecto> objetivos/mi-proyecto
# Requisitos/historias para el paso 5 (gaps), si el proyecto no los trae:
#   objetivos/mi-proyecto/REQUISITOS.md
OBJETIVO=objetivos/mi-proyecto docker compose --profile seguridad run --rm semgrep-objetivo
```

En PowerShell: `$env:OBJETIVO="objetivos/mi-proyecto"; docker compose --profile seguridad run --rm semgrep-objetivo`.

Luego, en Copilot Chat: `/metodologia objetivos/mi-proyecto` o
`/sast salida/reportes/semgrep-objetivo.sarif`. Guía completa: [`COPILOT.md`](../COPILOT.md).

## Varios proyectos y varias ejecuciones (modo agente)

Cuando se analizan **varios proyectos** o se corre **varias veces el mismo** (a medida que se
corrige), usa el modo `--run` de `metodologia.py` para que las salidas **no se pisen** y cada
una sea rastreable:

```bash
python3 agente-sast-g7/scripts/metodologia.py todo objetivos/mi-proyecto --run
```

- Escribe en `salida/reportes/metodologia/<proyecto>/<run_id>/candidatos-*.json`.
- `<proyecto>` = nombre de la carpeta (o `--proyecto <slug>`).
- `<run_id>` = `timestamp + commit del proyecto objetivo` (o `--run-id <id>`). El commit
  **ancla cada corrida al estado exacto del código**, así distingues las ejecuciones del
  mismo proyecto mientras se va corrigiendo.
- Mantiene `salida/reportes/metodologia/<proyecto>/latest` → última corrida y un
  `_indice.json` con el historial de corridas del proyecto.
- Además, **cada JSON lleva dentro** `proyecto`, `run_id`, `timestamp` y `commit`, de modo
  que el archivo es autodescriptivo aunque se mueva.

> Nota: el `commit` se lee del repo git que contenga al objetivo. Si clonas cada proyecto como
> su propio repo en `objetivos/`, será el commit de ese proyecto (lo correcto). Sin `--run`, el
> comportamiento anterior (archivos planos en `salida/reportes/metodologia/`) sigue igual.
