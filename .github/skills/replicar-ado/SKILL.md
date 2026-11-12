---
name: replicar-ado
description: "Replica este repo en otro Azure DevOps (crea el repo, sube main, crea el pipeline de seguridad y la política de PR), lo ejecuta, lo sigue y descarga los reportes. Simula primero (--dry-run) y pide confirmación antes de cada acción externa."
argument-hint: "<https://dev.azure.com/ORG> <PROYECTO>"
disable-model-invocation: true
---
# Replicar en otro Azure DevOps

Acciones externas: **pide confirmación explícita** antes de crear, subir o encolar nada.
**Nunca pidas un PAT en el chat** ni lo escribas en archivos; prefiere `az login`.

## 0. Datos
Del texto después de `/replicar-ado`: la **organización** (`https://dev.azure.com/ORG`; si
dan solo `ORG`, complétala) y el **proyecto** (debe existir). Si falta alguno, pregúntalo
una sola vez. Terminal: PowerShell → `./scripts/agente.ps1`; bash → `./scripts/agente.sh`.
Solo Docker: Azure CLI corre en un contenedor; nunca instales nada.

## Pasos
1. **Chequeo rápido:** `./scripts/agente.sh rapido`. Si falla, detente y pregunta.
2. **Cambios sin commit:** `git status`. Solo viaja lo commiteado en `main`; avisa si hay cambios.
3. **Login:** `./scripts/agente.sh ado-login` (el usuario completa el código en el
   navegador). Alternativa: un PAT que el usuario exporta él mismo en
   `AZURE_DEVOPS_EXT_PAT`.
4. **Simulacro:** `./scripts/agente.sh replicar <ORG> <PROYECTO>` (solo consultas). Muestra
   el resultado y **espera un "sí"**.
5. **Real:** `./scripts/agente.sh replicar <ORG> <PROYECTO> --real` (idempotente: crea solo
   lo que falta).
6. **Pipeline** (consume minutos; pide confirmación):
   `./scripts/agente.sh pipeline ejecutar --rama main --si --org <ORG> --project <PROYECTO>`,
   luego `pipeline seguir <ID> ...` hasta que termine y `pipeline descargar <ID> ...`
   (reportes en `salida/reportes/pipeline-<ID>/CodeAnalysisLogs/`). Si queda en cola sin agente, la
   organización necesita paralelismo hospedado: https://aka.ms/azpipelines-parallelism-request.
7. **Informe:** enlaces al repo y al pipeline, resultado por job y dónde quedaron los
   reportes. Ofrece analizarlos con `/sast salida/reportes/pipeline-<ID>/CodeAnalysisLogs/semgrep.sarif`.

Detalle de las etapas en `.github/agents/orquestador-pruebas.agent.md` (B y C).
