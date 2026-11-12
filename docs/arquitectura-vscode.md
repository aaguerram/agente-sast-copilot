# Arquitectura: ejecución desde VS Code

Cómo funciona el flujo cuando se ejecuta desde **VS Code con GitHub Copilot**: qué
piezas intervienen, dónde corre cada una y qué datos pasan entre ellas.

La regla de fondo: **en la máquina solo hacen falta git, Docker y VS Code con Copilot.**
Copilot no ejecuta herramientas de seguridad por sí mismo; lanza los scripts del repo
en la terminal de VS Code, y estos levantan contenedores con `docker compose`.

## Vista general

```mermaid
flowchart LR
    U([Persona]) -->|chat / skill /| VS

    subgraph VS["VS Code + GitHub Copilot"]
        direction TB
        INS[".github/copilot-instructions.md<br/>reglas del repo"]
        ORQ["Agente<br/>orquestador-pruebas"]
        P0["/demo · /ayuda"] --> MET
        P1["/validar-local"] --> ORQ
        P2["/replicar-ado"] --> ORQ
        P3["/sast"] --> SAST
        ORQ -->|subagentes| SAST
        subgraph SAST["Cadena de agentes SAST"]
            direction LR
            R[receptor-sast] --> PR[priorizador-cwe-owasp] --> RE[remediador] --> DA[devils-advocate]
        end
        MET["Agente<br/>metodologia-sast"]
        P4["/metodologia<br/>/metodologia-paso"] --> MET
        ORQ -->|etapa D| MET
        subgraph PASOS["Metodología SAST descompuesta (sobre el código)"]
            direction LR
            M1[ranking-archivos] & M2[mapeo-entradas] & M3[mapeo-operaciones] --> M4[trazador-flujos]
            M5[analizador-gaps]
        end
        MET -->|subagentes| PASOS
        PASOS -->|flujos y gaps| DA
        INS -.-> ORQ & SAST & MET
    end

    ORQ -->|comandos en la terminal| SH

    subgraph HOST["Máquina local (solo git + Docker)"]
        direction TB
        SH["scripts/agente.sh · agente.ps1<br/>validar-local · ado · ado-bootstrap · ado-pipeline"]
        DC["docker compose<br/>perfiles: seguridad · tools · agentes · ado"]
        SH --> DC
        DC --> C1[pre-commit + hooks .NET]
        DC --> C2[gitleaks]
        DC --> C3[Semgrep CE]
        DC --> C4[SonarQube efímero<br/>+ SDK .NET]
        DC --> C5[MkDocs]
        DC --> C6[API rickmorty-clean]
        DC --> C7[py: scripts de agentes]
        DC --> C8[az CLI]
        OUT[("salida/reportes/<br/>SARIF · JSON · logs · resumen.md")]
        C1 & C2 & C3 & C4 & C6 --> OUT
        C7 --> OUT
    end

    OUT -->|lee resultados| ORQ
    OUT -->|SARIF| SAST

    C8 -->|"git push · REST API<br/>(con confirmación)"| ADO

    subgraph ADO["Azure DevOps (cualquier organización)"]
        direction TB
        REPO[Repo Git · main] --> POL[Política de PR<br/>Build validation]
        POL --> PIPE["azure-pipelines.yml<br/>pre-commit · Semgrep · SonarQube"]
        PIPE --> ART[(Artefacto<br/>CodeAnalysisLogs)]
        WI[Boards: work items]
    end

    ART -->|ado-pipeline.sh descargar| OUT
    C7 -->|"crear_incidencias_ado.py<br/>(con aprobación)"| WI
```

## Componentes

| Capa | Pieza | Dónde vive | Qué hace |
|---|---|---|---|
| Interfaz | VS Code + GitHub Copilot (modo agente) | Máquina | Chat, selección de agente, aprobación de comandos |
| Reglas | `copilot-instructions.md` | `.github/` | Reglas comunes: solo Docker, sin secretos, Fortify como herramienta oficial, revisión humana |
| Orquestación | `orquestador-pruebas` | `.github/agents/` | Etapas A–D, checklist, confirmaciones antes de acciones externas |
| Skills (comandos `/`) | `/ayuda`, `/demo`, `/metodologia`, `/metodologia-paso`, `/sast`, `/validar-local`, `/replicar-ado` | `.github/skills/<nombre>/SKILL.md` | Arrancan una etapa concreta; sin argumentos usan la muestra vulnerable. Los `.prompt.md` de `.github/prompts/` solo remiten a ellas (compatibilidad) |
| Análisis | `receptor-sast` → `priorizador-cwe-owasp` → `remediador` → `devils-advocate` | `.github/agents/` | Normalizar, clasificar CWE/OWASP, proponer corrección, refutar falsos positivos |
| Metodología | `metodologia-sast` + `ranking-archivos`, `mapeo-entradas`, `mapeo-operaciones`, `trazador-flujos`, `analizador-gaps` | `.github/agents/` | Analiza el **código**: flujos entre capas y gaps contra requisitos; un paso o todos ([detalle](metodologia-sast.md)) |
| Ejecución | `agente` (punto de entrada único), `validar-local`, `ado`, `ado-bootstrap`, `ado-pipeline` (en `.sh` y `.ps1`), `sonar-analizar.sh` | `scripts/` | Envuelven `docker compose`; detectan SO, UID/GID, grupo de Docker y puertos |
| Herramientas | Servicios de `docker-compose.yml` | Contenedores | pre-commit, gitleaks, Semgrep, SonarQube, MkDocs, API, Python, az |
| Reglas propias | Hooks .NET, reglas Semgrep | `tools/pre-commit-hooks/`, `.semgrep/` | Lo que SonarQube Community no cubre ([detalle](hooks-dotnet.md)) |
| Código a analizar | Muestra vulnerable y proyectos del concurso | `agente-sast-g7/samples/app-vulnerable/`, `objetivos/<proyecto>/` (no versionado) | Objetivo de la ejecución real de los agentes; fuera de los gates bloqueantes. SARIF con el servicio `semgrep-objetivo` |
| Resultados | Reportes | `salida/reportes/` (no versionado) | Entrada de la cadena SAST y evidencia para la persona |
| Remoto | Repo, pipeline, política de PR, Boards | Azure DevOps | Los mismos controles en cada PR a `main`; incidencias |

## Flujo de una ejecución completa

```mermaid
sequenceDiagram
    autonumber
    actor P as Persona
    participant O as orquestador-pruebas<br/>(Copilot)
    participant T as Terminal VS Code
    participant D as docker compose
    participant A as Azure DevOps
    participant S as Cadena SAST

    P->>O: /validar-local
    O->>T: ./scripts/validar-local.sh
    T->>D: 8 fases en contenedores
    D-->>T: salida/reportes/ + resumen.md
    O-->>P: tabla Fase → Resultado → Evidencia

    P->>O: /replicar-ado ORG PROYECTO
    O->>T: ./scripts/ado.sh az login --use-device-code
    P-->>T: completa el login en el navegador
    O->>T: ado-bootstrap.sh --dry-run
    O-->>P: qué se crearía · ¿confirmas?
    P->>O: sí
    O->>T: ado-bootstrap.sh (sin --dry-run)
    T->>A: repo · push main · pipeline · política de PR

    O-->>P: ¿encolo el pipeline? (consume minutos)
    P->>O: sí
    O->>T: ado-pipeline.sh ejecutar --si / seguir
    A-->>T: resultado por job
    O->>T: ado-pipeline.sh descargar
    T-->>O: SARIF en salida/reportes/pipeline-ID/

    O->>S: delega con los SARIF
    S-->>P: hallazgos priorizados, remediación,<br/>falsos positivos descartados
    P->>S: aprueba crear incidencias
    S->>T: crear_incidencias_ado.py (--dry-run, luego real)
    T->>A: work items en Boards
```

## Fases locales (`validar-local.sh`)

```mermaid
flowchart LR
    A[pre-commit<br/>+ 15 hooks .NET] --> B[hooks-tests] --> C[gitleaks<br/>historial] --> D[Semgrep CE<br/>bloqueante] --> E[semgrep-demo<br/>+ normalizar] --> F[SonarQube<br/>efímero] --> G[docs<br/>mkdocs --strict] --> H[api<br/>build + smoke]
    H --> R[(resumen.md<br/>código 0 / 1)]
```

Cada fase es un servicio de `docker compose` y deja su log en
`salida/reportes/logs/<fase>.log`. Las mismas versiones (pre-commit 4.7.0, gitleaks
v8.30.1, Semgrep 1.185.0, .NET 10) corren en `azure-pipelines.yml`, así que lo que pasa
en local pasa en el PR.

## Límites de confianza

| Frontera | Control |
|---|---|
| Copilot → terminal | VS Code pide aprobar cada comando (salvo que la persona lo autorice); el agente solo usa los scripts del repo |
| Máquina → Azure DevOps | Siempre `--dry-run` primero y confirmación explícita antes de crear repo, push, pipeline, ejecuciones o work items |
| Credenciales | `az login` con código de dispositivo, sesión en `~/.azure` del host. Un PAT solo en la variable `AZURE_DEVOPS_EXT_PAT`, nunca en archivos, chat ni logs |
| Hallazgos → incidencias | `devils-advocate` refuta antes; la persona aprueba; no se parchea código automáticamente |
| Host | No se instala nada: los contenedores montan el repo y, para SonarQube, el socket de Docker |

## Requisitos para ejecutarlo en VS Code

1. git, Docker con el plugin `docker compose`, y el usuario en el grupo `docker`
   (en Windows: Git for Windows, Docker Desktop con WSL2 y **PowerShell 7**).
2. VS Code con **GitHub Copilot** y **Copilot Chat** en modo agente.
3. Abrir la **raíz del repo** como carpeta del workspace (y confiar en ella): Copilot solo
   carga `.github/agents/` y `.github/skills/` de la raíz.
4. En el chat, escribir `/demo` (o `/ayuda`), o elegir un agente del desplegable de agentes
   (no el de modelo) y escribir `ejecuta`.

### Windows o Linux

Los scripts existen en bash (`.sh`) y PowerShell 7 (`.ps1`) con las mismas fases y
códigos de salida. El agente mira qué terminal tiene VS Code (PowerShell en Windows, bash
en Linux/macOS) y usa la versión que corresponde; la tabla de equivalencias está en
`.github/copilot-instructions.md`. Debajo de los scripts todo es igual: `docker compose`
con contenedores Linux. Para SonarQube, el contenedor que orquesta se une a la red del
servidor efímero y el SDK hereda el montaje del repo (`--volumes-from`), así que no
depende de rutas `C:\...` ni de la red del host.

```mermaid
flowchart LR
    W["Windows<br/>PowerShell 7 · *.ps1"] --> DC
    L["Linux / macOS<br/>bash · *.sh"] --> DC
    DC["docker compose<br/>(Docker Desktop o Docker Engine)"] --> K["Mismos contenedores Linux<br/>y mismos reportes"]
```

Para montarlo desde cero en otra máquina y otra organización, ver
[Replicar en otra máquina](replicar.md).
