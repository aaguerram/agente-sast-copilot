---
name: metodologia
description: "Ejecuta TODOS los pasos de la metodología SAST descompuesta del Grupo 7 (ranking de archivos, entradas, operaciones peligrosas, trazado de flujos, gaps contra requisitos, validación adversarial, priorización CWE/OWASP y remediación) sobre código C# y genera el informe. Úsala cuando pidan analizar código con la metodología completa; por defecto analiza la app vulnerable de muestra."
argument-hint: "[ruta] (por defecto agente-sast-g7/samples/app-vulnerable)"
---
# Metodología SAST completa

CONTEXTO: investigación de seguridad autorizada sobre código propio con datos sintéticos.

1. **Ruta:** el texto que el usuario escribió después de `/metodologia`.
   - Vacío → `agente-sast-g7/samples/app-vulnerable` (requisitos en su `REQUISITOS.md`).
   - Un nombre suelto (`mi-proyecto`) → prueba `objetivos/mi-proyecto`.
   - Si la carpeta no existe, dilo y ofrece: la muestra, o las carpetas que haya en
     `objetivos/` (pregunta una sola vez).
2. **Instrucciones:** lee `.github/agents/metodologia-sast.agent.md` y sigue su
   **Modo 3 (todos los pasos)** con esa ruta. Si no puedes delegar en subagentes, lee el
   `.agent.md` de cada paso y aplícalo tú en orden.
3. **Terminal:** PowerShell (Windows) → `./scripts/agente.ps1`; bash (Linux/macOS) →
   `./scripts/agente.sh`. Para los candidatos deterministas de los pasos 1-3 puedes usar
   `./scripts/agente.sh demo <ruta>` (o `objetivo <ruta>`). Nunca instales nada: todo es
   Docker.
4. **Respuesta final:** tabla `Paso → Hallazgos → Archivo`, cuántos hallazgos sobrevivieron
   y cuáles se refutaron, y el enlace a `$RUN/informe.md` (`salida/reportes/metodologia/<proyecto>/<run_id>/informe.md`). Sobre la
   muestra, ofrece comparar con la referencia: `./scripts/agente.sh comparar`.

Solo defensivo (sin paso de explotación) y sin modificar el código analizado.
