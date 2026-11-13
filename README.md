# agente_pruebas_copilot

Repositorio único de trabajo del agente de pruebas (HackaPro 2026, Grupo 7 · SAST):
documentación, API de ejemplo, agentes y pipeline de seguridad.

> **¿Vas a usarlo con GitHub Copilot?** Abre la raíz del repo en VS Code y escribe
> **`/demo`** en el chat (o **`/ayuda`** para ver el menú). En la terminal:
> `./scripts/agente.sh demo` (Windows: `./scripts/agente.ps1 demo`). Todas las
> combinaciones en [`COPILOT.md`](COPILOT.md), siempre sobre código con vulnerabilidades
> (la muestra `agente-sast-g7/samples/app-vulnerable/` o un proyecto real en
> [`objetivos/`](objetivos/README.md)).
>
> **Metodología paso a paso** (entradas, proceso, validación, salidas y ejemplos):
> [`agente-sast-g7/METODOLOGIA.md`](agente-sast-g7/METODOLOGIA.md). **Presentación:**
> [`docs/datos/agente-sast-g7.pptx`](docs/datos/agente-sast-g7.pptx).

## Estructura

| Carpeta / archivo | Contenido |
|---|---|
| `docs/`, `mkdocs.yml`, `docker-compose.yml`, `tools/` | Sitio de documentación MkDocs Material |
| `rickmorty-clean/` | API REST .NET 10 de ejemplo (data quemada, 8 endpoints). [README](rickmorty-clean/README.md) |
| `agente-sast-g7/` | Scripts SARIF → incidencias y muestra vulnerable de la cadena SAST. [README](agente-sast-g7/README.md) |
| `.github/` | GitHub Copilot: agentes (`agents/`: cadena SAST, `orquestador-pruebas`, `metodologia-sast` y un agente por paso), skills (`skills/`: `/ayuda`, `/demo`, `/metodologia`, `/metodologia-paso`, `/sast`, `/validar-local`, `/replicar-ado`) y prompts de compatibilidad (`prompts/`) |
| `azure-pipelines.yml` | pre-commit + gitleaks, Semgrep CE y SonarQube Community en cada PR a `main` |
| `objetivos/` | Proyectos reales del concurso a analizar (no se versionan, fuera de los gates). [README](objetivos/README.md) |
| `COPILOT.md` | Guía de uso de los agentes en Copilot Chat |
| `agente-sast-g7/METODOLOGIA.md` | Metodología SAST en detalle: cada paso, archivos de entrada y salida, validación y ejemplos |
| `docs/datos/agente-sast-g7.pptx` | Presentación del Grupo 7 (también en el sitio de docs, página *Presentación*) |
| `scripts/` | `agente` (punto de entrada único: `demo`, `rapido`, `validar`, `objetivo`, `comparar`, `ado-login`, `replicar`, `pipeline`), `validar-local` (todas las fases en local), `ado-bootstrap` + `ado` (subir a Azure DevOps), `ado-pipeline` (ejecutar, seguir y descargar el pipeline), `imagenes` (exportar / cargar las imágenes para una máquina sin internet), cada uno en `.sh` (bash) y `.ps1` (PowerShell 7, Windows); `sonar-analizar.sh` (SonarQube) |

## Pipeline de seguridad

Cada pull request a `main` ejecuta los tres controles y no se puede completar si alguno
falla. Detalle, variables y limitaciones en [`docs/pipeline.md`](docs/pipeline.md).

En local solo se necesitan **git y Docker**; cada herramienta corre en su contenedor:

```bash
./scripts/validar-local.sh                     # pre-commit, hooks, gitleaks, Semgrep, demo SAST,
                                               # SonarQube, docs y API -> salida/reportes/resumen.md
./scripts/validar-local.sh --saltar sonarqube  # más rápido
```

En **Windows** (Docker Desktop + PowerShell 7) los mismos scripts existen como `.ps1`:

```powershell
./scripts/validar-local.ps1
./scripts/validar-local.ps1 -Saltar sonarqube
```

Requisitos y equivalencias en [`docs/replicar.md`](docs/replicar.md#windows).

### Máquina sin internet

Las imágenes traen dentro las reglas de Semgrep, los hooks de pre-commit, el scanner de
SonarQube y los paquetes NuGet: en la máquina destino solo se ejecuta `docker compose`.

```bash
./scripts/imagenes.sh exportar     # máquina CON internet -> imagenes-sast.tar (PowerShell: imagenes.ps1)
./scripts/imagenes.sh cargar       # máquina SIN internet: docker load + verificación
./scripts/agente.sh objetivo objetivos/mi-proyecto --sin-dotnet   # solo código, sin compilar
SIN_INTERNET=1 ./scripts/validar-local.sh
```

`--sin-dotnet` omite los analizadores de seguridad .NET, el único paso que compila el
proyecto (necesita sus paquetes NuGet); con `SIN_INTERNET=1` se omiten solos. Semgrep y la
metodología analizan el código fuente tal cual.

Guía paso a paso: [`exportar-imagenes-offline.md`](exportar-imagenes-offline.md).

## Replicar en otro Azure DevOps

Con un proyecto ya creado (Azure CLI corre en un contenedor; no hay que instalarlo):

```bash
./scripts/ado.sh az login --use-device-code
./scripts/ado.sh ./scripts/ado-bootstrap.sh --org https://dev.azure.com/MI_ORG --project MI_PROYECTO --dry-run
./scripts/ado.sh ./scripts/ado-bootstrap.sh --org https://dev.azure.com/MI_ORG --project MI_PROYECTO
```

En PowerShell: `./scripts/ado.ps1 az login --use-device-code` y
`./scripts/ado-bootstrap.ps1 -Org https://dev.azure.com/MI_ORG -Project MI_PROYECTO -DryRun`.

Crea el repositorio, sube `main`, crea el pipeline y la política de PR. Es idempotente.
Guía completa de cero: [`docs/replicar.md`](docs/replicar.md).

## Agentes y skills de Copilot

Abre la raíz del repo en VS Code y, en el chat de Copilot:

| Escribe | Hace |
|---|---|
| `/ayuda` | Menú con todos los comandos |
| `/demo` | Metodología SAST completa sobre la app vulnerable y comparación con la referencia |
| `/metodologia [ruta]` · `/metodologia-paso <paso> [ruta]` | Todos los pasos o uno (ranking, entradas, operaciones, flujos, gaps, validación adversarial, priorización, remediación) |
| `/sast [reporte.sarif]` | Cadena SAST sobre un reporte (Semgrep, SonarQube, Fortify) |
| `/validar-local [rápido]` | Todas las fases locales |
| `/replicar-ado <org> <proyecto>` | Replicar en otro Azure DevOps, con simulacro y confirmación |

O elige un agente del desplegable (`orquestador-pruebas`, `metodologia-sast` o el de un
paso) y escribe `ejecuta`: sin más datos usa la muestra vulnerable. Los comandos `/` son
skills nativas (`.github/skills/`); ver [`COPILOT.md`](COPILOT.md) y
[`docs/metodologia-sast.md`](docs/metodologia-sast.md).

En la terminal, el mismo menú: `./scripts/agente.sh` (PowerShell: `./scripts/agente.ps1`).
Las bases del hackathon no se versionan: se copian a mano en `docs/datos/`
(ver [`docs/pipeline.md`](docs/pipeline.md)).

## Documentación (MkDocs)

```bash
docker compose up -d --build         # http://localhost:8300
docker compose run --rm docs-build   # sitio estático en salida/sitio.zip
```

- **Markdown:** archivos `.md` en `docs/`; agrégalos al `nav` de `mkdocs.yml`. El sitio se recarga solo.
- **Presentaciones:** copia el `.pptx` a `docs/datos/` y enlázalo desde un `.md`:
  `[Título](visor/ppt.html?f=datos/archivo.pptx){ target=_blank .md-button }`
  (la ruta a `visor/` es relativa al `.md`; `f` es relativa a `docs/`).
- **Otros visores** en `docs/visor/`: `pdf.html`, `excel.html`, `word.html`, `drawio.html`, `json.html`.
- **Puerto:** `DOCS_PORT` en `.env` (ver `.env.example`).

Páginas: [`docs/ssdlc.md`](docs/ssdlc.md), [`docs/hackapro.md`](docs/hackapro.md),
[`docs/recomendaciones.md`](docs/recomendaciones.md), [`docs/pipeline.md`](docs/pipeline.md),
[`docs/arquitectura-vscode.md`](docs/arquitectura-vscode.md),
[`docs/hooks-dotnet.md`](docs/hooks-dotnet.md), [`docs/replicar.md`](docs/replicar.md),
[`docs/metodologia-sast.md`](docs/metodologia-sast.md).
