# Uso con GitHub Copilot

Guía práctica para ejecutar los agentes de este repo desde **VS Code con GitHub Copilot
Chat (modo agente)**: qué hay, qué escribir en el chat en cada caso y qué resultado esperar.

> **Siempre sobre código con vulnerabilidades.** El concurso valida la **ejecución real**
> de los agentes. Ejecútalos sobre código que tenga fallas: la muestra
> `agente-sast-g7/samples/app-vulnerable/` (por defecto) o un proyecto real del concurso
> clonado en `objetivos/<proyecto>/`. `rickmorty-clean` es la API **limpia** del pipeline
> y no sirve como demostración de hallazgos.

> Qué hace cada paso, qué archivos lee y escribe, y cómo se valida:
> `agente-sast-g7/METODOLOGIA.md`. Presentación: `docs/datos/agente-sast-g7.pptx`.

## Inicio en 3 pasos

1. **Abre la raíz del repo** en VS Code (`File > Open Folder` → `agente_pruebas_copilot`) y
   confía en la carpeta si VS Code lo pregunta (en *Restricted Mode* no se cargan agentes
   ni skills). Docker debe estar arrancado.
2. Abre el chat de Copilot (`Ctrl+Alt+I`; macOS `Ctrl+Cmd+I`) y escribe **`/demo`**.
   Ejecuta la metodología completa sobre la app vulnerable de muestra y la compara con la
   respuesta de referencia. Acepta los comandos que te proponga (**Allow / Continue**).
3. Para un proyecto real: `git clone <url> objetivos/mi-proyecto` y en el chat
   **`/metodologia objetivos/mi-proyecto`**.

¿Perdido? Escribe **`/ayuda`** en el chat o ejecuta `./scripts/agente.sh` en la terminal.

### Comandos copiables

| Quiero… | Chat de Copilot | Terminal Linux/macOS | Terminal Windows (PowerShell 7) |
|---|---|---|---|
| Menú de ayuda | `/ayuda` | `./scripts/agente.sh` | `./scripts/agente.ps1` |
| Demo completa (código vulnerable) | `/demo` | `./scripts/agente.sh demo` ¹ | `./scripts/agente.ps1 demo` ¹ |
| Los 8 pasos de la metodología | `/metodologia` | — | — |
| Un solo paso | `/metodologia-paso 4` | — | — |
| Proyecto real del concurso | `/metodologia objetivos/mi-proyecto` | `./scripts/agente.sh objetivo objetivos/mi-proyecto` ¹ | `./scripts/agente.ps1 objetivo objetivos/mi-proyecto` ¹ |
| Cadena SAST sobre un SARIF | `/sast` | — | — |
| Comparar con la referencia | — | `./scripts/agente.sh comparar` | `./scripts/agente.ps1 comparar` |
| Validar todo (rápido, sin SonarQube) | `/validar-local rápido` | `./scripts/agente.sh rapido` | `./scripts/agente.ps1 rapido` |
| Validar todo (completo) | `/validar-local` | `./scripts/agente.sh validar` | `./scripts/agente.ps1 validar` |
| Login en Azure DevOps | — | `./scripts/agente.sh ado-login` | `./scripts/agente.ps1 ado-login` |
| Replicar en otro Azure DevOps (simulacro) | `/replicar-ado https://dev.azure.com/ORG PROYECTO` | `./scripts/agente.sh replicar https://dev.azure.com/ORG PROYECTO` | `./scripts/agente.ps1 replicar https://dev.azure.com/ORG PROYECTO` |
| … de verdad | (el agente pide confirmación) | `… replicar … --real` | `… replicar … --real` |
| Seguir el pipeline de un PR | — | `./scripts/agente.sh pipeline seguir --pr 12 --org … --project …` | `./scripts/agente.ps1 pipeline seguir --pr 12 --org … --project …` |

¹ En la terminal solo corre la parte determinista (candidatos de los pasos 1-3, Semgrep y
la comparación). El razonamiento de los pasos 4-8 lo hace Copilot con `/demo` o `/metodologia`.

> **Siempre sobre código con vulnerabilidades.** El concurso valida la **ejecución real**
> de los agentes. Ejecútalos sobre código que tenga fallas: la muestra
> `agente-sast-g7/samples/app-vulnerable/` (por defecto) o un proyecto real del concurso
> clonado en `objetivos/<proyecto>/`. `rickmorty-clean` es la API **limpia** del pipeline
> y no sirve como demostración de hallazgos.

## 1. Preparación

1. Instala **git**, **Docker** (en Windows: Docker Desktop con backend WSL2) y **VS Code**
   con **GitHub Copilot** y **GitHub Copilot Chat**. En Windows, además, **PowerShell 7**.
2. Clona el repo y abre **la carpeta raíz** en VS Code. Copilot carga los agentes de
   `.github/agents/` y las skills de `.github/skills/` de la raíz del workspace.
3. En el chat, abajo hay dos desplegables: el de **agentes** (`Agent`, `Ask`, `Plan` y los
   agentes del repo) y el de **modelo** (p. ej. *Copilot Fusion · Standard*; cualquiera
   sirve). Puedes elegir un agente del primero **o** escribir una skill con `/`.
4. Cuando Copilot pida ejecutar un comando, revísalo y acéptalo. Los agentes piden
   confirmación explícita antes de cualquier acción externa (push, pipeline, incidencias).

No se instala nada más: pre-commit, gitleaks, Semgrep, SonarQube, .NET, Python y Azure CLI
corren en contenedores con `docker compose`. Si la política de ejecución de Windows bloquea
los scripts: `Unblock-File ./scripts/*.ps1` o `pwsh -ExecutionPolicy Bypass -File ./scripts/agente.ps1`.

### Skills y prompts (VS Code 1.144+)

Los comandos con `/` son **skills nativas** en `.github/skills/<nombre>/SKILL.md`: funcionan
en el arnés **Copilot** (el actual) y en el **Local**. Los `.prompt.md` de
`.github/prompts/` se mantienen solo por compatibilidad con versiones anteriores de VS
Code y remiten a la skill del mismo nombre: hacen exactamente lo mismo.

- Si VS Code muestra **Review Migrations / Convert Prompt to Skills**, no hace falta
  convertir nada: las skills ya existen. Puedes elegir **Ignore**.
- Si ya lo convertiste y aparecieron carpetas propias en `.github/skills/` o en
  `~/.copilot/skills/`, bórralas antes de `git pull` (o `git stash -u`), o verás comandos
  duplicados.

### Comandos de terminal (detalle)

`./scripts/agente.sh` (bash) y `./scripts/agente.ps1` (PowerShell 7) son el punto de entrada
único. Envuelven los scripts de siempre, que siguen disponibles:

| Subcomando | Equivale a |
|---|---|
| `validar [--solo a,b \| --saltar x \| --listar]` | `./scripts/validar-local.sh` (`.ps1`: `-Solo`, `-Saltar`, `-Listar`) |
| `rapido` | `./scripts/validar-local.sh --saltar sonarqube` |
| `demo [ruta]` / `objetivo <ruta>` | `metodologia.py todo` + servicio `semgrep-objetivo` + analizadores .NET (lo mismo que `dotnet`) + `comparar_esperado.py` |
| `demo`/`objetivo` … `--sin-dotnet` | Lo mismo **sin compilar**: omite los analizadores .NET y analiza solo el código fuente. Con `SIN_INTERNET=1` se omiten solos |
| `dotnet [ruta]` | Solo el servicio `dotnet-objetivo` (analizadores de seguridad .NET; **compila** el proyecto) + `normalizar_sarif.py` → `salida/reportes/dotnet-normalizado.json` |
| `comparar` | `agente-sast-g7/scripts/comparar_esperado.py` |
| `ado-login` | `./scripts/ado.sh az login --use-device-code` |
| `replicar <org> <proy> [--real]` | `./scripts/ado.sh ./scripts/ado-bootstrap.sh … [--dry-run]` |
| `pipeline <sub>` | `./scripts/ado.sh ./scripts/ado-pipeline.sh <sub>` |

Organización y proyecto para `pipeline`: `--org`/`--project` o las variables `ADO_ORG_URL`
y `ADO_PROJECT`.

## 2. Agentes y skills

| Nombre | Tipo | Para qué | Cómo se invoca |
|---|---|---|---|
| `/ayuda` | skill | Menú con todos los comandos | `/ayuda` |
| `/demo` | skill | Metodología completa sobre la muestra + comparación con `esperado/` | `/demo` |
| `/metodologia` | skill | Los 8 pasos + informe | `/metodologia [ruta]` |
| `/metodologia-paso` | skill | Un paso (número, nombre o alias) | `/metodologia-paso <paso> [ruta]` |
| `/sast` | skill | Cadena SAST sobre un reporte SARIF | `/sast [reporte.sarif]` |
| `/validar-local` | skill | Todas las fases locales | `/validar-local [rápido \| solo … \| saltar …]` |
| `/replicar-ado` | skill | Replicar en otra organización (solo a mano: no se activa sola) | `/replicar-ado <https://dev.azure.com/ORG> <PROYECTO>` |
| `orquestador-pruebas` | agente | Flujo completo: validar (A), replicar (B), pipeline (C), análisis (D) | Desplegable de agentes → `ejecuta` |
| `metodologia-sast` | agente | Metodología SAST: un paso o todos, con informe | Desplegable → `todo`, `paso 3`, `demo` |
| `ranking-archivos` | agente (paso 1) | Ordena archivos por riesgo | Desplegable → `ejecuta`, o `/metodologia-paso 1` |
| `mapeo-entradas` | agente (paso 2) | Datos que llegan del cliente y si se validan | `/metodologia-paso 2` |
| `mapeo-operaciones` | agente (paso 3) | Operaciones peligrosas (SQL, comandos, rutas, deserialización, SSRF, redirecciones, logs) | `/metodologia-paso 3` |
| `trazador-flujos` | agente (paso 4) | Sigue el dato de la entrada a la operación entre archivos y capas | `/metodologia-paso 4` |
| `analizador-gaps` | agente (paso 5) | Controles que faltan según los requisitos (autorización, reglas de negocio) | `/metodologia-paso 5` |
| `devils-advocate` | agente (paso 6) | Intenta refutar cada hallazgo para quitar falsos positivos | `/metodologia-paso 6` |
| `priorizador-cwe-owasp` | agente (paso 7) | CWE, OWASP y prioridad | `/metodologia-paso 7` |
| `remediador` | agente (paso 8) | Corrección propuesta por hallazgo | `/metodologia-paso 8` |
| `receptor-sast` | agente | Valida y normaliza un SARIF | Lo usa `/sast` |

Cada agente funciona solo con elegirlo y escribir algo mínimo (`ejecuta`, `todo`,
`paso 3`, `demo`): sin más datos usa la app vulnerable de muestra.

## 3. Combinaciones de ejecución

Los tiempos son aproximados: dependen de la máquina, de la red (la primera vez se
descargan imágenes) y, en los pasos con razonamiento, del modelo.

### 3.1 Flujo completo (A → D)

Elige el agente **`orquestador-pruebas`** y escribe:

```text
Ejecuta el flujo completo sobre agente-sast-g7/samples/app-vulnerable
```

- **Hace:** A) `validar-local` (9 fases); B) si quieres, replica en otro Azure DevOps
  (`--dry-run` primero y confirmación); C) ejecuta, sigue y descarga el pipeline;
  D) analiza los SARIF con `/sast` y el código con `/metodologia`, y previsualiza
  incidencias.
- **Produce:** `salida/reportes/` (A), `salida/reportes/pipeline-<ID>/` (C),
  `salida/reportes/metodologia/` y `salida/reportes/validado.json` (D).
- **Tarda:** 30–60 min con todo; sin B y C, 20–30 min.

### 3.2 Solo validación local

| Escribe | Hace | Tarda |
|---|---|---|
| `/validar-local` | Las 9 fases: pre-commit, hooks-tests, gitleaks, semgrep, semgrep-demo, metodologia, sonarqube, docs, api | 8–15 min |
| `/validar-local --saltar sonarqube` | Todas menos SonarQube (la más lenta) | 3–5 min |
| `/validar-local --solo semgrep-demo,metodologia` | Solo los reportes de demo sobre las muestras vulnerables | 1–2 min |

- **Produce:** `salida/reportes/resumen.md`, `salida/reportes/logs/<fase>.log` y los
  reportes `gitleaks.sarif`, `semgrep.sarif`, `semgrep-muestras.sarif`,
  `muestras-normalizado.json`, `sonar.sarif`, `metodologia/candidatos-*.json`.
- En Windows el agente traduce las opciones (`-Saltar sonarqube`, `-Solo a,b`).

### 3.3 Metodología completa

```text
/metodologia
/metodologia objetivos/mi-proyecto
```

- **Hace:** pasos 1→8 delegando en cada agente y escribe el informe.
- **Produce:** en `salida/reportes/metodologia/`: `ranking.json`, `entradas.json`,
  `operaciones.json`, `flujos.json`, `gaps.json`, `validacion.json`, `priorizacion.json`,
  `remediacion.json` e `informe.md`.
- **Tarda:** 10–25 min.

### 3.4 Un paso puntual

```text
/metodologia-paso <paso> [ruta]
```

`<paso>` acepta el número, el nombre del agente o el alias. Sin argumentos muestra el menú.

| # | Alias | Agente | ¿Corre solo? | Necesita | Genera |
|---|---|---|---|---|---|
| 1 | `ranking` | `ranking-archivos` | Sí | ruta | `ranking.json` |
| 2 | `entradas` | `mapeo-entradas` | Sí | ruta (usa 1 si existe) | `entradas.json` |
| 3 | `operaciones` | `mapeo-operaciones` | Sí | ruta | `operaciones.json` |
| 4 | `flujos` | `trazador-flujos` | No | 2 y 3 | `flujos.json` |
| 5 | `gaps` | `analizador-gaps` | Sí, con requisitos | ruta + `REQUISITOS.md` | `gaps.json` |
| 6 | `validacion` | `devils-advocate` | No | 4 y/o 5 | `validacion.json` |
| 7 | `priorizacion` | `priorizador-cwe-owasp` | No | 6 | `priorizacion.json` |
| 8 | `remediacion` | `remediador` | No | 7 | `remediacion.json` |
| — | `informe` | `metodologia-sast` | No | lo que exista | `informe.md` |

Pasos que corren solos (1–3 min cada uno):

```text
/metodologia-paso ranking
/metodologia-paso 2
/metodologia-paso operaciones objetivos/mi-proyecto
/metodologia-paso gaps
```

Pasos que dependen de otros: si faltan sus entradas, el agente lo dice y ofrece
generarlas antes. Por ejemplo, en una carpeta de resultados vacía:

```text
Tú:      /metodologia-paso flujos
Agente:  El paso 4 necesita entradas.json y operaciones.json, que no existen para
         agente-sast-g7/samples/app-vulnerable. ¿Ejecuto antes los pasos 2 y 3?
Tú:      sí
```

Lo mismo con `validacion` (pide 4 y/o 5), `priorizacion` (pide 6) y `remediacion` (pide 7).
Si las dependencias existen pero son de **otra ruta**, las regenera: no mezcla resultados.

### 3.5 Combinaciones parciales útiles

| Objetivo | Qué escribir |
|---|---|
| Solo flujos de datos (1→2→3→4) | `/metodologia-paso flujos` y acepta generar 2 y 3; o ejecuta `ranking`, `entradas`, `operaciones` y `flujos` en orden |
| Solo gaps contra requisitos (5) | `/metodologia-paso gaps [ruta]` |
| Validación adversarial de lo encontrado (4+5→6) | `/metodologia-paso flujos`, `/metodologia-paso gaps` y después `/metodologia-paso validacion` |
| De lo validado a la corrección (6→7→8) | `/metodologia-paso validacion`, `/metodologia-paso priorizacion`, `/metodologia-paso remediacion` |
| Varios pasos en un mensaje | Agente `metodologia-sast`: `Ejecuta los pasos 2, 3 y 4 sobre objetivos/mi-proyecto` |

### 3.6 Cadena SAST sobre un reporte (SARIF)

```text
/sast salida/reportes/semgrep-muestras.sarif
/sast salida/reportes/semgrep-objetivo.sarif
/sast salida/reportes/pipeline-<ID>/CodeAnalysisLogs/semgrep.sarif
/sast <ruta>/fortify.sarif
```

- **Hace:** normaliza (`receptor-sast`) → prioriza (`priorizador-cwe-owasp`) → propone
  correcciones (`remediador`) → refuta (`devils-advocate`) → previsualiza incidencias.
- **Produce:** `salida/reportes/normalizado.json`, `priorizado.json`, `remediacion.json`,
  `validado.json`.
- **Tarda:** 5–10 min.
- Cómo obtener el SARIF: `/validar-local --solo semgrep-demo` (muestra), el servicio
  `semgrep-objetivo` (proyecto real, ver sección 4), el artefacto del pipeline (3.7) o el
  reporte de Fortify.

### 3.7 Replicar en otro Azure DevOps

```text
/replicar-ado https://dev.azure.com/OTRA_ORG OTRO_PROYECTO
```

- **Hace:** validación rápida → login (`az login --use-device-code`, lo completas tú en el
  navegador) → `ado-bootstrap --dry-run` → con tu confirmación crea repo, sube `main`,
  pipeline y política de PR → con tu confirmación ejecuta el pipeline, lo sigue y descarga
  el artefacto.
- **Produce:** el repo y el pipeline en la otra organización;
  `salida/reportes/pipeline-<ID>/CodeAnalysisLogs/`.
- **Tarda:** 15–25 min (el pipeline, unos 8–12). Una organización nueva necesita
  paralelismo hospedado: https://aka.ms/azpipelines-parallelism-request.

### 3.8 Crear incidencias en Azure Boards

Solo con lo que sobrevivió al `devils-advocate` y siempre con previsualización:

```text
Agente orquestador-pruebas: Crea las incidencias de salida/reportes/validado.json
```

1. El agente ejecuta
   `docker compose --profile agentes run --rm py agente-sast-g7/scripts/crear_incidencias_ado.py salida/reportes/validado.json --dry-run`
   y te muestra qué crearía.
2. Solo con tu "sí" lo repite sin `--dry-run`.
3. `ADO_ORG_URL`, `ADO_PROJECT` y `ADO_PAT` los defines tú en tu terminal o en
   `agente-sast-g7/.env` (no versionado). Nunca escribas el PAT en el chat.

## 4. Ejecución real sobre un proyecto con vulnerabilidades

### Muestra incluida (por defecto)

`agente-sast-g7/samples/app-vulnerable/` es una API .NET de un banco ficticio con fallas
a propósito: 10 flujos vulnerables, 1 flujo saneado (para que `devils-advocate` lo
refute) y 10 gaps contra su `REQUISITOS.md`. El inventario está en su `README.md`. Todos
los comandos la usan si no indicas ruta.

### Proyecto real del concurso

1. Clónalo **dentro del workspace**, en `objetivos/`:

    ```bash
    git clone <url-del-proyecto> objetivos/mi-proyecto
    ```

    `objetivos/` no se versiona y queda fuera de pre-commit, gitleaks, Semgrep bloqueante
    y SonarQube, así un proyecto vulnerable no rompe el pipeline de este repo.
    Alternativa: `File > Add Folder to Workspace` (workspace multi-raíz), indicando la ruta
    completa al agente; los agentes y prompts siguen saliendo de la carpeta de este repo.

2. Requisitos para el paso 5 (gaps): deja historias de usuario, reglas de negocio o un
   modelo de amenazas en `objetivos/mi-proyecto/REQUISITOS.md`, o indica al agente dónde
   están. Sin requisitos, el paso 5 se omite.

3. SARIF del proyecto con Semgrep y candidatos de los pasos 1-3 (1–3 min):

    ```bash
    ./scripts/agente.sh objetivo objetivos/mi-proyecto      # PowerShell: ./scripts/agente.ps1 objetivo ...
    ```

    Genera `salida/reportes/semgrep-objetivo.sarif`, `salida/reportes/objetivo-normalizado.json`
    (rutas relativas a la raíz del repo) y `salida/reportes/metodologia/candidatos-*.json`.
    Equivale a `OBJETIVO=objetivos/mi-proyecto docker compose --profile seguridad run --rm semgrep-objetivo`
    más `metodologia.py todo`.

    El mismo comando añade una tercera fuente SARIF si el proyecto tiene `.csproj`:
    analizadores de seguridad .NET (`CA2100`, `CA3001`–`CA3012`, `CA2300`–`CA2330`,
    `CA5350`–`CA5403`), con CWE y OWASP completados desde la base de conocimiento. Genera
    `salida/reportes/dotnet-objetivo/*.sarif` y `salida/reportes/dotnet-normalizado.json`.
    Es el **único paso que compila** el proyecto (necesita sus paquetes NuGet); si no compila,
    avisa y el análisis sigue sin esa fuente.

    **Solo con el código, sin compilar** (y siempre en una máquina sin internet):

    ```bash
    ./scripts/agente.sh objetivo objetivos/mi-proyecto --sin-dotnet   # PowerShell: ./scripts/agente.ps1 objetivo ... --sin-dotnet
    ```

    Con `SIN_INTERNET=1` en el entorno el paso se omite solo. Para ejecutar únicamente los
    analizadores: `./scripts/agente.sh dotnet objetivos/mi-proyecto`.

4. En el chat:

    ```text
    /metodologia objetivos/mi-proyecto
    /sast salida/reportes/semgrep-objetivo.sarif
    ```

## 5. Verificar el resultado

- **Comparación automática:** `./scripts/agente.sh comparar` (o `/demo`, que la incluye)
  muestra, paso a paso, cuántos elementos hay frente a la referencia y qué fallas
  esperadas encontraron los candidatos deterministas.
- **Muestra:** compara `salida/reportes/metodologia/` con la ejecución de referencia en
  `agente-sast-g7/samples/app-vulnerable/esperado/` (un JSON por paso e `informe.md`):
  8 archivos de riesgo Alto, 15 entradas, 15 operaciones, 11 flujos (1 saneado), 10 gaps,
  20 hallazgos que sobreviven (16 de prioridad Alta) y 20 recomendaciones. Lo esperado
  está en `esperado/fallas-esperadas.json`.
- **Variabilidad:** los pasos 4–8 los razona el modelo; los números pueden variar entre
  ejecuciones. Lo importante es que aparezcan los flujos y gaps del inventario y que el
  flujo saneado (F-11) se refute.
- **Un paso sin hallazgos:** el agente lo dice explícitamente y no inventa. Sobre la
  muestra eso indica un problema (ruta equivocada o resultados de otra ruta); sobre un
  proyecto real puede ser legítimo, revisa los `candidatos-*.json` del script.
- **Script determinista:** `agente-sast-g7/scripts/metodologia.py` genera los candidatos de
  los pasos 1–3 con un campo `confianza` (`alta`: el argumento viene de un parámetro o de
  `Request`; `media`: origen no determinado).

## 6. Problemas frecuentes

| Síntoma | Solución |
|---|---|
| No aparecen los agentes ni los comandos `/…` | Abre la **raíz** del repo (no una subcarpeta); sal de *Restricted Mode* (**Trust**); `Ctrl+Shift+P` → **Developer: Reload Window**; revisa **Chat: Open Customizations** (pestañas Agents y Skills); actualiza VS Code y Copilot Chat |
| Solo veo *Copilot Fusion* / *Standard* | Es el selector de **modelo**. Los agentes están en el **otro** desplegable (`Agent`/`Ask`/`Plan`) |
| Los prompts se convierten solos en skills | Es la migración de VS Code 1.144+; el repo ya trae las skills nativas: elige **Ignore** (ver sección 1) |
| Copilot no ejecuta comandos | Acepta la ejecución en el chat (**Continuar**); revisa que la herramienta de terminal esté habilitada para el agente |
| `Docker no responde` o `permission denied` en el socket | Arranca Docker / Docker Desktop; en Linux tu usuario debe estar en el grupo `docker` |
| Windows: "running scripts is disabled" | `Unblock-File ./scripts/*.ps1` o `pwsh -ExecutionPolicy Bypass -File ...`; usa PowerShell 7 |
| `az`: sin sesión o 401 | `./scripts/agente.sh ado-login` (o `agente.ps1`); el PAT solo en la variable `AZURE_DEVOPS_EXT_PAT` de tu terminal |
| El pipeline queda en cola | La organización no tiene paralelismo hospedado: https://aka.ms/azpipelines-parallelism-request |
| Un paso dice que faltan dependencias | Es lo esperado en pasos 4, 6, 7, 8: acepta generarlas o ejecuta antes los pasos indicados |
| Puerto ocupado (SonarQube, API) | `SONAR_PORT` en `.env` (def. 9100); la API busca sola un puerto libre |

Más detalle: `agente-sast-g7/METODOLOGIA.md` (cada paso con entradas, proceso, validación, salidas y ejemplos), `docs/metodologia-sast.md`, `docs/arquitectura-vscode.md`, `docs/replicar.md`.
