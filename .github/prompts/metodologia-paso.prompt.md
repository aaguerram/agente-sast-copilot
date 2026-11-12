---
name: metodologia-paso
description: "Ejecuta UN paso de la metodología SAST (1 ranking … 8 remediación, o informe). Si le falta algo, lo dice y ofrece generarlo. (Compatibilidad: la lógica está en la skill .github/skills/metodologia-paso/.)"
argument-hint: "<paso: 1-8, nombre o alias> [ruta]"
agent: metodologia-sast
---
Lee `.github/skills/metodologia-paso/SKILL.md` y sigue sus instrucciones al pie de la letra.

Lo que el usuario escribió después de `/metodologia-paso` son los argumentos de esa skill; si no
escribió nada, usa los valores por defecto que indica la skill.
