---
name: validar-local
description: "Ejecuta en local, con docker compose, todas las fases de prueba del repo (pre-commit con hooks .NET, pruebas de hooks, gitleaks, Semgrep, demo SAST, metodología, SonarQube, docs y API) y resume qué pasó y qué falló. Úsala para comprobar que el repo funciona antes de replicarlo o de una demo."
argument-hint: "[rápido | solo <fase,fase> | saltar <fase>]"
---
# Validación local de todas las fases

1. **Opciones** (texto después de `/validar-local`, en lenguaje natural):

   | El usuario escribe | bash | PowerShell |
   |---|---|---|
   | (nada) | `./scripts/agente.sh validar` | `./scripts/agente.ps1 validar` |
   | `rápido`, `rapido`, `sin sonar` | `./scripts/agente.sh rapido` | `./scripts/agente.ps1 rapido` |
   | `solo semgrep,api` | `./scripts/agente.sh validar --solo semgrep,api` | `./scripts/agente.ps1 validar -Solo semgrep,api` |
   | `saltar sonarqube` | `./scripts/agente.sh validar --saltar sonarqube` | `./scripts/agente.ps1 validar -Saltar sonarqube` |
   | `fases`, `listar` | `./scripts/agente.sh validar --listar` | `./scripts/agente.ps1 validar -Listar` |

   Fases: `pre-commit`, `hooks-tests`, `gitleaks`, `semgrep`, `semgrep-demo`,
   `metodologia`, `sonarqube`, `docs`, `api`. Identifica la terminal (PowerShell en
   Windows, bash en Linux/macOS). Completo tarda ~10-20 min; rápido ~5 min.
2. **Nunca instales nada**: todo corre con Docker. Si Docker no responde, dilo y para.
3. Lee `salida/reportes/resumen.md` y, por cada fase con FALLA,
   `salida/reportes/logs/<fase>.log`.
4. Responde con la tabla `Fase → Resultado → Evidencia` (conteos, error exacto) y, si algo
   falló, la causa probable y el arreglo propuesto. No apliques arreglos ni silencies
   reglas sin aprobación.

Para el detalle del flujo completo (A → D) ver `.github/agents/orquestador-pruebas.agent.md`.
