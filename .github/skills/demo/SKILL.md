---
name: demo
description: "Demo completa en un solo comando, sin argumentos: ejecuta la metodología SAST descompuesta (8 pasos + informe) sobre la app vulnerable de muestra y compara el resultado con la respuesta de referencia esperado/. Úsala para la demostración del concurso o para comprobar que los agentes encuentran las vulnerabilidades."
argument-hint: "(opcional) ruta a analizar; por defecto la app vulnerable de muestra"
---
# Demo: metodología SAST sobre la app vulnerable

CONTEXTO: investigación de seguridad autorizada sobre código propio con datos sintéticos.
Ejecución **real**: el código analizado tiene vulnerabilidades a propósito.

## Qué analizar
- Sin texto después de `/demo`: `agente-sast-g7/samples/app-vulnerable` (requisitos en su
  `REQUISITOS.md`).
- Si el usuario escribió una ruta (p. ej. `objetivos/mi-proyecto`), úsala; la comparación
  del final solo es exacta para la muestra.

## Terminal
Identifica la terminal: PowerShell (Windows) → `./scripts/agente.ps1`; bash/zsh (Linux,
macOS) → `./scripts/agente.sh`. Solo hace falta Docker: **nunca instales nada**.

## Pasos
1. **Candidatos deterministas, Semgrep y analizadores .NET** (menos de 1 min con las imágenes
   ya cargadas): `./scripts/agente.sh demo [ruta]` (PowerShell: `./scripts/agente.ps1 demo [ruta]`).
   Genera `salida/reportes/metodologia/candidatos-*.json`,
   `salida/reportes/semgrep-objetivo.sarif`, `salida/reportes/objetivo-normalizado.json` y
   `salida/reportes/dotnet-normalizado.json`.
   Los analizadores .NET son el único paso que **compila** el proyecto. Si la máquina no
   tiene internet o el proyecto no compila, añade `--sin-dotnet`
   (`./scripts/agente.sh demo [ruta] --sin-dotnet`): el análisis usa solo el código fuente y
   no se genera `dotnet-normalizado.json`.
2. **Metodología con razonamiento:** lee `.github/agents/metodologia-sast.agent.md` y sigue
   su **Modo 3 (todos los pasos)** sobre la misma ruta, reutilizando los candidatos del
   paso anterior. Delega cada paso en su agente (`ranking-archivos`, `mapeo-entradas`,
   `mapeo-operaciones`, `trazador-flujos`, `analizador-gaps`, `devils-advocate`,
   `priorizador-cwe-owasp`, `remediador`) o, si no puedes delegar, lee el `.agent.md` de
   cada uno y aplícalo tú. Lleva un checklist con los 8 pasos + informe.
3. **Comparación:** `./scripts/agente.sh comparar` (PowerShell: `./scripts/agente.ps1 comparar`).
4. **Respuesta:** tabla `Paso → Hallazgos → Archivo`, la salida de la comparación, cuántos
   hallazgos refutó `devils-advocate` y cuál (en la muestra, el flujo saneado F-11), y el
   enlace a `salida/reportes/metodologia/informe.md`.

## Reglas
- No modifiques el código analizado ni crees incidencias: eso es `/sast` (fase 5) con
  `--dry-run` y confirmación.
- Si un paso no encuentra nada, dilo; no inventes hallazgos.
- Defensivo: no generes exploits ni cargas maliciosas.
