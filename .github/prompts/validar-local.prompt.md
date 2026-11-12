---
name: validar-local
description: "Ejecuta todas las fases de prueba en local con docker compose (pre-commit, hooks, gitleaks, Semgrep, demo SAST, metodología, SonarQube, docs, API) y resume el resultado. (Compatibilidad: la lógica está en la skill .github/skills/validar-local/.)"
argument-hint: "[rápido | solo <fase,fase> | saltar <fase>]"
agent: orquestador-pruebas
---
Lee `.github/skills/validar-local/SKILL.md` y sigue sus instrucciones al pie de la letra.

Lo que el usuario escribió después de `/validar-local` son los argumentos de esa skill; si no
escribió nada, usa los valores por defecto que indica la skill.
