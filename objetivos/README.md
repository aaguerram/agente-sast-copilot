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
