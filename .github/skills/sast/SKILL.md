---
name: sast
description: "Cadena SAST del Grupo 7 sobre un REPORTE de herramienta (SARIF de Semgrep, SonarQube, gitleaks o Fortify): normaliza, prioriza por CWE/OWASP, propone remediación, valida adversarialmente y, con aprobación, crea incidencias en Azure DevOps. Úsala cuando haya un reporte .sarif que analizar; sin argumentos usa el último reporte generado."
argument-hint: "[ruta al reporte .sarif]"
---
# Cadena SAST sobre un reporte

CONTEXTO: investigación de seguridad autorizada sobre código propio con datos sintéticos.
Lee `.github/copilot-instructions.md` antes de empezar.

`/sast` trabaja sobre **reportes de herramientas**. Para analizar el **código** con la
metodología descompuesta (flujos entre archivos, gaps contra requisitos) usa `/metodologia`.

## 0. Qué reporte usar
El texto después de `/sast` es la ruta del reporte. Si no hay, usa el primero que exista:
1. `salida/reportes/semgrep-objetivo.sarif` (lo genera `/demo` o `./scripts/agente.sh demo|objetivo`)
2. `salida/reportes/semgrep-muestras.sarif`
3. Si no existe ninguno, genéralo: `./scripts/agente.sh demo` (PowerShell:
   `./scripts/agente.ps1 demo`) y usa `salida/reportes/semgrep-objetivo.sarif`.

También sirven `semgrep.sarif`, `sonar.sarif`, `gitleaks.sarif` de `salida/reportes/`, los
descargados del pipeline en `salida/reportes/pipeline-<id>/CodeAnalysisLogs/`, o un SARIF de Fortify.

Comandos: solo Docker, nunca instales nada. Abreviatura:
`PY = docker compose --profile agentes run --rm py`

## Fase 1 — Recepción y normalización
`PY agente-sast-g7/scripts/normalizar_sarif.py <reporte> -o salida/reportes/normalizado.json`.
Valida el resultado siguiendo `.github/agents/receptor-sast.agent.md`. Si no hay
hallazgos, dilo y termina.

## Fase 2 — Priorización
Según `.github/agents/priorizador-cwe-owasp.agent.md`: CWE/OWASP y prioridad sobre
`normalizado.json` → `salida/reportes/priorizado.json`.

## Fase 3 — Remediación
Según `.github/agents/remediador.agent.md` → `salida/reportes/remediacion.json`. No
modifiques el código fuente.

## Fase 4 — Validación adversarial
Según `.github/agents/devils-advocate.agent.md`: intenta refutar cada hallazgo y marca
`sobrevive` / `refutado` → `salida/reportes/validado.json`.

## Fase 5 — Incidencias (Human-in-the-Loop)
Muestra los hallazgos Alta/Crítica que sobrevivieron. Primero previsualiza:
`PY agente-sast-g7/scripts/crear_incidencias_ado.py salida/reportes/validado.json --dry-run`.
Solo con confirmación explícita, sin `--dry-run`. `ADO_ORG_URL`, `ADO_PROJECT` y `ADO_PAT`
los define el usuario en su entorno o en `agente-sast-g7/.env` (ver
`agente-sast-g7/docs/ADO-CREDENCIALES.md`); **nunca pidas el PAT en el chat**.

## Entregables
- `salida/reportes/normalizado.json`, `priorizado.json`, `remediacion.json`, `validado.json`.
- Matrices: Hallazgo→Severidad→Archivo→Línea, Hallazgo→CWE→OWASP→Prioridad,
  Hallazgo→Ubicación→Recomendación.
