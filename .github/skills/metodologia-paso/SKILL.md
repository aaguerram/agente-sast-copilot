---
name: metodologia-paso
description: "Ejecuta UN paso de la metodología SAST (1 ranking, 2 entradas, 3 operaciones, 4 flujos, 5 gaps, 6 validación adversarial, 7 priorización, 8 remediación, o el informe). Comprueba si el paso puede correr solo y, si le falta algo, lo dice y ofrece generarlo antes. Úsala cuando pidan un paso concreto, p. ej. 'paso 4', 'trazador' o 'solo los gaps'."
argument-hint: "<paso: 1-8, nombre o alias> [ruta]"
---
# Un paso de la metodología SAST

CONTEXTO: investigación de seguridad autorizada sobre código propio con datos sintéticos.

## 1. Interpreta lo que escribió el usuario después de `/metodologia-paso`
Acepta lenguaje natural. El **paso** puede venir como número, nombre del agente o alias:

| Paso | Agente | Se reconoce por |
|---|---|---|
| 1 | `ranking-archivos` | `1`, `paso 1`, `ranking`, `archivos`, `riesgo` |
| 2 | `mapeo-entradas` | `2`, `entradas`, `fuentes`, `inputs` |
| 3 | `mapeo-operaciones` | `3`, `operaciones`, `sumideros`, `sinks`, `peligrosas` |
| 4 | `trazador-flujos` | `4`, `flujos`, `trazador`, `trazado`, `taint` |
| 5 | `analizador-gaps` | `5`, `gaps`, `requisitos`, `brechas`, `logica` |
| 6 | `devils-advocate` | `6`, `validacion`, `adversarial`, `refutar`, `devils` |
| 7 | `priorizador-cwe-owasp` | `7`, `priorizacion`, `prioridad`, `cwe`, `owasp` |
| 8 | `remediador` | `8`, `remediacion`, `correccion`, `fix` |
| — | `metodologia-sast` | `informe`, `reporte final` |

La **ruta** es cualquier texto que parezca una carpeta; si no hay, usa
`agente-sast-g7/samples/app-vulnerable`. Un nombre suelto (`mi-proyecto`) → `objetivos/mi-proyecto`.

Si no se reconoce el paso, muestra la tabla y pregunta **una sola vez** cuál ejecutar.

## 2. Ejecuta
Lee `.github/agents/metodologia-sast.agent.md` y sigue su **Modo 2 (un paso puntual)**:
- Pasos 1, 2, 3 y 5 corren solos (el 5 usa `<ruta>/REQUISITOS.md` o, si no hay, OWASP ASVS de `agente-sast-g7/kb/asvs-requisitos.md`).
- Pasos 4, 6, 7 y 8 dependen de otros: si faltan sus JSON en `salida/reportes/metodologia/`
  (o son de otra ruta), dilo y ofrece generar antes **solo lo que falta**.
- Para ejecutar el paso, lee `.github/agents/<agente>.agent.md` y aplícalo (o delega en ese
  agente como subagente si puedes).

Terminal: PowerShell → `./scripts/agente.ps1`; bash → `./scripts/agente.sh`. Nunca instales
nada: todo es Docker.

## 3. Responde
Tabla del paso (hallazgos con archivo:línea) y la ruta del JSON generado. Sugiere el
siguiente paso lógico (p. ej. tras el 4: `/metodologia-paso 6`).
