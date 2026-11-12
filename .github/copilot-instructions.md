# Agente de pruebas — Grupo 7 · HackaPro 2026 (SAST)

Este repo implementa el **Grupo 7 · Análisis de Pruebas SAST**: una cadena de agentes que
**consume** reportes SAST y propone remediación, sin reemplazar la herramienta oficial, más
el pipeline de seguridad (pre-commit + gitleaks, Semgrep CE, SonarQube Community) que se
puede replicar en cualquier Azure DevOps.

## Cómo se ejecuta todo (reglas del entorno)

- **Solo git y Docker en la máquina.** Todo corre con `docker compose`; no instales
  herramientas (ni `pip install`, ni `az`, ni `dotnet`) en el host.
- **Punto de entrada único:** `./scripts/agente.sh <subcomando>` (PowerShell: `./scripts/agente.ps1`):
  `validar`, `rapido`, `demo [ruta]`, `objetivo <ruta>`, `comparar`, `ado-login`,
  `replicar <org> <proy> [--real]`, `pipeline <sub>`. Sin argumentos muestra la ayuda.
- Validación local de todas las fases: `./scripts/validar-local.sh` (o `.ps1`) → `salida/reportes/`.
- Azure CLI en contenedor: `./scripts/ado.sh <comando>` (o `.ps1`).
- Scripts Python de los agentes: `docker compose --profile agentes run --rm py <script> ...`.
- Rutas: los scripts de la cadena SAST están en `agente-sast-g7/scripts/`; los reportes
  generados van a `salida/reportes/` (no se versiona).
- **Skills** (`.github/skills/<nombre>/SKILL.md`, comandos `/` en el chat): `/ayuda`,
  `/demo`, `/metodologia`, `/metodologia-paso`, `/sast`, `/validar-local`, `/replicar-ado`.
  Los `.prompt.md` de `.github/prompts/` solo remiten a la skill del mismo nombre
  (compatibilidad con VS Code anterior). El texto que el usuario escribe después del
  comando son los argumentos; sin argumentos, cada skill usa valores por defecto.
- Agente que orquesta el flujo completo: `orquestador-pruebas`.
- **Valores por defecto:** si el usuario no da detalles (`ejecuta`, `todo`, `demo`), trabaja
  sobre `agente-sast-g7/samples/app-vulnerable/` y pregunta una sola vez solo lo
  imprescindible (organización y proyecto de Azure DevOps).
- **Ejecución real:** los agentes se ejecutan sobre código CON vulnerabilidades: la
  muestra `agente-sast-g7/samples/app-vulnerable/` o un proyecto del concurso clonado en
  `objetivos/<proyecto>/` (no se versiona y queda fuera de los gates). SARIF de un
  objetivo: `./scripts/agente.sh objetivo <ruta>` (o
  `OBJETIVO=<ruta> docker compose --profile seguridad run --rm semgrep-objetivo`).
  Guía de uso para personas: `COPILOT.md`.
- Metodología SAST descompuesta sobre el código: agente `metodologia-sast`
  (skills `/metodologia [ruta]`, `/metodologia-paso <paso> [ruta]` y `/demo`); resultados en
  `salida/reportes/metodologia/`; comparación con la referencia: `./scripts/agente.sh comparar`.
- **Carpeta de la corrida (`$RUN`) — varios proyectos y varias ejecuciones.** Para no pisar
  resultados entre proyectos ni entre corridas del mismo proyecto (a medida que se corrige),
  cada ejecución vive en `$RUN = salida/reportes/metodologia/<proyecto>/<run_id>/`:
  - `<proyecto>` = nombre de la carpeta objetivo (`app-vulnerable`, el de `objetivos/<proyecto>/`…).
  - `<run_id>` = `timestamp-commit` del proyecto objetivo. Lo fija **una sola vez** el agente
    `metodologia-sast` (o `orquestador-pruebas`) al inicio de la corrida y se pasa **igual a
    todos los pasos** con `--run --proyecto <proyecto> --run-id <run_id>`.
  - **Todas las rutas `salida/reportes/metodologia/<archivo>` que aparecen en los agentes se
    entienden bajo `$RUN`** (p. ej. `entradas.json` → `$RUN/entradas.json`). Los `candidatos-*.json`
    y cada JSON de paso llevan dentro `proyecto`, `run_id`, `timestamp` y `commit`, así que son
    rastreables por sí solos. `metodologia.py` crea `$RUN`, un puntero `latest/` a la última
    corrida y un `_indice.json` con el historial del proyecto.
  - La ruta plana `salida/reportes/metodologia/<archivo>` (sin `<proyecto>/<run_id>`) queda para
    la demo de un único proyecto; en modo agente con objetivos reales, usa siempre `$RUN`.
- Delegación: pide a cada agente del paso que actúe como subagente cuando tu entorno lo
  permita; si no, lee su `.agent.md` y aplícalo tú. No dependas de nombres de herramientas
  de un arnés concreto.

## Windows, Linux o macOS: qué script usar

Cada script de `scripts/` existe en dos versiones con las mismas fases, reportes y
códigos de salida. **Antes del primer comando, identifica la terminal**: si es PowerShell
(lo normal en VS Code sobre Windows) usa los `.ps1`; si es bash/zsh, los `.sh`. En caso de
duda, ejecuta `$PSVersionTable.PSVersion` (PowerShell) o `uname -s` (bash). En Windows se
necesita **PowerShell 7** (`pwsh`), no Windows PowerShell 5.1.

| Tarea | bash (Linux/macOS) | PowerShell 7 (Windows; también Linux/macOS) |
|---|---|---|
| **Atajo para todo** | `./scripts/agente.sh <subcomando>` | `./scripts/agente.ps1 <subcomando>` |
| Demo / proyecto real (pasos 1-3 deterministas + Semgrep) | `./scripts/agente.sh demo` · `objetivo objetivos/<p>` | `./scripts/agente.ps1 demo` · `objetivo objetivos/<p>` |
| Comparar con la referencia | `./scripts/agente.sh comparar` | `./scripts/agente.ps1 comparar` |
| Validar todas las fases | `./scripts/validar-local.sh` | `./scripts/validar-local.ps1` |
| Saltar o elegir fases | `--saltar sonarqube` · `--solo semgrep,api` · `--listar` | `-Saltar sonarqube` · `-Solo semgrep,api` · `-Listar` |
| Azure CLI en contenedor | `./scripts/ado.sh az login --use-device-code` | `./scripts/ado.ps1 az login --use-device-code` |
| Replicar en Azure DevOps | `./scripts/ado.sh ./scripts/ado-bootstrap.sh --org <ORG> --project <PROY> --dry-run` | `./scripts/ado-bootstrap.ps1 -Org <ORG> -Project <PROY> -DryRun` |
| Pipeline (ejecutar, seguir, descargar, estado-pr) | `./scripts/ado.sh ./scripts/ado-pipeline.sh --org <ORG> --project <PROY> seguir --pr <n>` | `./scripts/ado-pipeline.ps1 --org <ORG> --project <PROY> seguir --pr <n>` (mismas opciones `--x`) |
| Scripts Python de los agentes | `docker compose --profile agentes run --rm py <script> ...` | igual (el comando es idéntico) |
| SARIF de un proyecto objetivo | `OBJETIVO=objetivos/<p> docker compose --profile seguridad run --rm semgrep-objetivo` | `$env:OBJETIVO="objetivos/<p>"; docker compose --profile seguridad run --rm semgrep-objetivo` |
| PAT solo en la sesión | `read -rs AZURE_DEVOPS_EXT_PAT && export AZURE_DEVOPS_EXT_PAT` | `$env:AZURE_DEVOPS_EXT_PAT = Read-Host -MaskInput` |

Los ejemplos de los agentes y skills usan la forma bash; tradúcelos con esta tabla.
Las rutas dentro de los contenedores siempre llevan `/` (p. ej. `agente-sast-g7/scripts/...`).

## Principios (no negociables)

- **Fortify es la herramienta SAST oficial.** Los agentes la *complementan*: consumen,
  normalizan, priorizan, enriquecen y proponen correcciones. No ejecutan el escaneo oficial.
- **Entrada normalizada en SARIF.** Así se aceptan de una vez Fortify, Semgrep y SonarQube.
  En sandbox se generan reportes con **Semgrep CE → SARIF**.
- **Razonamiento descompuesto.** Cada agente hace *una* cosa; la síntesis ocurre en el
  pipeline, no dentro de un solo agente (evita alucinaciones).
- **Validación adversarial obligatoria.** Antes de crear incidencias, el *devil's advocate*
  intenta refutar cada hallazgo para filtrar falsos positivos.
- **Human-in-the-Loop.** Ninguna corrección sugerida por IA se aplica sola; una persona la
  revisa. Se registra incidencia, no se parchea automáticamente el código.
- **Seguridad.** Nunca escribir secretos en código, logs, reportes ni prompts. El PAT de
  Azure DevOps se lee de variables de entorno. Solo datos sintéticos.

## Lenguaje objetivo

`.NET / C#`. Los rulesets de Semgrep y los ejemplos de remediación son para C#.

## Cadena de agentes

1. `receptor-sast` — valida y normaliza el SARIF a JSON común.
2. `priorizador-cwe-owasp` — clasifica CWE/OWASP y asigna prioridad.
3. `remediador` — propone corrección por vulnerabilidad, con referencia a estándar.
4. `devils-advocate` — intenta refutar cada hallazgo; sobreviven los no refutados.
5. Automatización (`agente-sast-g7/scripts/crear_incidencias_ado.py`) — crea work items Crítica/Alta en
   Azure DevOps, sin duplicar.

## Metodología SAST descompuesta (sobre el código)

Agente `metodologia-sast`; cada paso es un agente con una sola responsabilidad:
`ranking-archivos` → `mapeo-entradas` → `mapeo-operaciones` → `trazador-flujos` →
`analizador-gaps` → `devils-advocate` → `priorizador-cwe-owasp` → `remediador`.
Los pasos 1, 2, 3 y 5 corren solos; 4, 6, 7 y 8 dependen de los anteriores. Apoyo
determinista: `agente-sast-g7/scripts/metodologia.py`. Muestra para la demo y respuesta de
referencia: `agente-sast-g7/samples/app-vulnerable/` y su carpeta `esperado/`.

## Mapeo de severidad (resuelve la inconsistencia de las bases)

| SARIF `level` | Severidad | Prioridad | ¿Crea incidencia? |
|---|---|---|---|
| `error` | Alta | Alta | Sí |
| `warning` | Media | Media | No (queda en reporte) |
| `note` | Baja | Baja | No |

Ajustar este mapeo si el banco define otra escala.
