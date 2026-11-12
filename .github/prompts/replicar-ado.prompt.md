---
name: replicar-ado
description: "Replica este repo en otro Azure DevOps, lo ejecuta y descarga los reportes. Simula primero y pide confirmación antes de cada acción externa. (Compatibilidad: la lógica está en la skill .github/skills/replicar-ado/.)"
argument-hint: "<https://dev.azure.com/ORG> <PROYECTO>"
agent: orquestador-pruebas
---
Lee `.github/skills/replicar-ado/SKILL.md` y sigue sus instrucciones al pie de la letra.

Lo que el usuario escribió después de `/replicar-ado` son los argumentos de esa skill; si no
escribió nada, usa los valores por defecto que indica la skill.
