---
name: ayuda
description: "Muestra el menú de este repo: qué comandos y agentes de Copilot hay, ejemplos listos para copiar (chat y terminal, Linux y Windows) y los pasos 1-8 de la metodología SAST con sus alias. Úsala cuando el usuario pregunte qué puede hacer, cómo empezar o qué comando usar."
argument-hint: "(sin argumentos)"
---
# Ayuda: menú del agente de pruebas (Grupo 7 · SAST)

No ejecutes nada. Responde con este menú tal cual (puedes acortarlo si el usuario pidió
algo concreto) y termina preguntando qué quiere ejecutar.

## Empieza aquí

| Quiero… | En el chat de Copilot | En la terminal (bash) | En la terminal (PowerShell) |
|---|---|---|---|
| Ver la demo completa sobre código vulnerable | `/demo` | `./scripts/agente.sh demo` | `./scripts/agente.ps1 demo` |
| Los 8 pasos de la metodología | `/metodologia` | — | — |
| Un solo paso | `/metodologia-paso 4` | — | — |
| Analizar un proyecto real del concurso | `/metodologia objetivos/<proyecto>` | `./scripts/agente.sh objetivo objetivos/<proyecto>` | `./scripts/agente.ps1 objetivo objetivos/<proyecto>` |
| Cadena SAST sobre un reporte SARIF | `/sast` | — | — |
| Validar todo en local (rápido) | `/validar-local rápido` | `./scripts/agente.sh rapido` | `./scripts/agente.ps1 rapido` |
| Validar todo en local (completo) | `/validar-local` | `./scripts/agente.sh validar` | `./scripts/agente.ps1 validar` |
| Replicar en otro Azure DevOps | `/replicar-ado https://dev.azure.com/ORG PROYECTO` | `./scripts/agente.sh replicar https://dev.azure.com/ORG PROYECTO` | `./scripts/agente.ps1 replicar https://dev.azure.com/ORG PROYECTO` |
| Ver esta ayuda | `/ayuda` | `./scripts/agente.sh` | `./scripts/agente.ps1` |

Sin argumentos, todo apunta a la app vulnerable de muestra
`agente-sast-g7/samples/app-vulnerable/`: el concurso valida la **ejecución real** sobre
código con vulnerabilidades. `replicar` sin `--real` solo simula.

## Agentes (desplegable de agentes del chat)

| Agente | Escribe algo como | Hace |
|---|---|---|
| `metodologia-sast` | `todo` · `paso 3` · `demo` | Metodología SAST descompuesta, un paso o todos |
| `orquestador-pruebas` | `ejecuta` | Validar en local → replicar en Azure DevOps → pipeline → análisis |
| `ranking-archivos` … `remediador` | `ejecuta` | Un paso concreto (1 a 8) |

## Pasos de la metodología (`/metodologia-paso <paso>`)

| # | Alias que entiende | Corre solo | Necesita |
|---|---|---|---|
| 1 | `ranking`, `archivos`, `riesgo` | Sí | — |
| 2 | `entradas`, `fuentes` | Sí | — |
| 3 | `operaciones`, `sumideros`, `peligrosas` | Sí | — |
| 4 | `flujos`, `trazador`, `trazado` | No | 2 y 3 |
| 5 | `gaps`, `requisitos`, `brechas` | Sí (con requisitos) | — |
| 6 | `validacion`, `devils-advocate`, `refutar` | No | 4 y/o 5 |
| 7 | `priorizacion`, `cwe`, `owasp` | No | 6 |
| 8 | `remediacion`, `correccion` | No | 7 |
| — | `informe` | No | lo que exista |

Si a un paso le falta algo, el agente lo dice y ofrece generarlo antes.

Resultados: `salida/reportes/metodologia/` (un JSON por paso + `informe.md`). Referencia
para comparar: `agente-sast-g7/samples/app-vulnerable/esperado/`. Guía completa:
`COPILOT.md`.
