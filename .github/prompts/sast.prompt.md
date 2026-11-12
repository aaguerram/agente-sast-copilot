---
name: sast
description: "Cadena SAST sobre un reporte SARIF: normaliza, prioriza, propone remediación, valida adversarialmente y, con aprobación, crea incidencias. (Compatibilidad: la lógica está en la skill .github/skills/sast/.)"
argument-hint: "[ruta al reporte .sarif]"
agent: orquestador-pruebas
---
Lee `.github/skills/sast/SKILL.md` y sigue sus instrucciones al pie de la letra.

Lo que el usuario escribió después de `/sast` son los argumentos de esa skill; si no
escribió nada, usa los valores por defecto que indica la skill.
