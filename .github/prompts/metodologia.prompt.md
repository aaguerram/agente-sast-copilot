---
name: metodologia
description: "Ejecuta TODOS los pasos de la metodología SAST descompuesta y genera el informe. Por defecto analiza la app vulnerable de muestra. (Compatibilidad: la lógica está en la skill .github/skills/metodologia/.)"
argument-hint: "[ruta] (por defecto la app vulnerable)"
agent: metodologia-sast
---
Lee `.github/skills/metodologia/SKILL.md` y sigue sus instrucciones al pie de la letra.

Lo que el usuario escribió después de `/metodologia` son los argumentos de esa skill; si no
escribió nada, usa los valores por defecto que indica la skill.
