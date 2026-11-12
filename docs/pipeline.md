# Pipeline de seguridad

Este es el **repositorio único de trabajo**: documentación, API de ejemplo, agentes SAST y
pipeline viven aquí. Cada *pull request* a `main` ejecuta **pre-commit + gitleaks**,
**Semgrep CE** y **SonarQube Community** en Azure Pipelines y no se puede completar si
alguno falla. Trivy queda fuera a propósito.

## Estructura del repositorio

| Carpeta / archivo | Contenido |
|---|---|
| `docs/`, `mkdocs.yml`, `docker-compose.yml`, `tools/` | Este sitio de documentación (MkDocs Material en Docker) |
| `rickmorty-clean/` | API REST .NET 10 de ejemplo (arquitectura limpia, data quemada, 8 endpoints). Es el código que analiza SonarQube |
| `agente-sast-g7/` | Agentes de GitHub Copilot del Grupo 7, scripts de normalización de SARIF y de creación de incidencias, y la muestra vulnerable |
| `azure-pipelines.yml` | Pipeline de seguridad |
| `.pre-commit-config.yaml`, `.gitleaks.toml` | Hooks de pre-commit y configuración de gitleaks |
| `tools/pre-commit-hooks/` | Hooks propios de buenas prácticas .NET y sus pruebas ([detalle](hooks-dotnet.md)) |
| `.semgrep/`, `.semgrepignore` | Reglas propias de Semgrep y exclusiones |
| `scripts/validar-local.sh` | Ejecuta en local todas las fases de prueba con docker compose |
| `scripts/ado-bootstrap.sh`, `scripts/ado.sh` | Sube el repo a Azure DevOps y crea pipeline y política de PR (Azure CLI en contenedor) |
| `.github/` | Agentes, skills (`/demo`, `/metodologia`, `/sast`…) y prompts de compatibilidad de GitHub Copilot, incluido el orquestador del flujo |
| `scripts/sonar-analizar.sh`, `scripts/sonar_a_sarif.py` | Análisis con SonarQube y exportación a JSON y SARIF |

## Qué ejecuta el pipeline

| Job | Qué hace | Bloquea cuando |
|---|---|---|
| `pre_commit` | Los hooks de `.pre-commit-config.yaml` sobre todos los archivos y gitleaks sobre el historial | Un hook falla o se encuentra un secreto |
| `semgrep` | Reglas del registro (`p/default`, `p/csharp`, `p/secrets`) más las de `.semgrep/` | Hay cualquier hallazgo |
| `sonarqube` | Levanta SonarQube Community en un contenedor, analiza `rickmorty-clean/RickMorty.sln` y exporta los hallazgos | Falla el *quality gate* o hay hallazgos `BLOCKER` o `CRITICAL` |

Los reportes quedan en el artefacto **`CodeAnalysisLogs`** de cada ejecución:

| Archivo | Origen |
|---|---|
| `gitleaks.sarif` | Secretos en el historial |
| `semgrep.sarif` | SAST del repositorio |
| `semgrep-muestras.sarif`, `muestras-normalizado.json` | Reporte **con hallazgos** sobre la muestra vulnerable, ya normalizado: entrada de demo para los agentes |
| `sonar.sarif`, `sonar-issues.json`, `sonar-hotspots.json`, `sonar-quality-gate.json` | SonarQube |

El pipeline no usa extensiones del Marketplace, *service connections* ni servidores
externos: por eso se replica en cualquier organización.

## Replicar en otra organización de Azure DevOps

### Requisitos

- Un **proyecto** ya creado en la organización de destino, con Azure Repos y Pipelines.
- **Capacidad de pipelines hospedados** en esa organización (al menos un job paralelo). En
  organizaciones nuevas hay que solicitarla a Microsoft; sin ella las ejecuciones quedan en
  cola. Con un agente propio, cambia `pool` en `azure-pipelines.yml`; el agente necesita
  Docker, Python 3 y salida a internet.
- En tu máquina: `git`, `curl`, `python3` y **una** de estas formas de autenticarte:
    - Azure CLI con `az login` de una cuenta con acceso a la organización, o
    - un PAT en la variable `AZURE_DEVOPS_EXT_PAT` con permisos *Code (Read & write)*,
      *Build (Read & execute)* y *Policy (Read & write)*... o acceso total.
- Permiso para crear repositorios, pipelines y políticas de rama en el proyecto.

### Pasos

1. Descarga o clona este repositorio. Si lo bajaste como ZIP, inicializa git:

    ```bash
    git init -b main && git add -A && git commit -m "Importar proyecto"
    ```

2. Ejecuta el *bootstrap* con tu organización y proyecto:

    ```bash
    ./scripts/ado-bootstrap.sh --org https://dev.azure.com/MI_ORG --project MI_PROYECTO
    ```

    Opcionales: `--repo NOMBRE` (por defecto, el nombre de la carpeta) y
    `--pipeline NOMBRE` (por defecto, `<repo>-seguridad`).

3. Abre un *pull request* a `main`: el pipeline arranca solo y aparece como comprobación
   obligatoria.

El script crea, solo si faltan, el repositorio, la rama `main`, el pipeline y la política
*Build validation*. Es idempotente y no borra ni cambia nada existente.

### Bases del hackathon (paso manual)

Las bases oficiales son un documento interno y **no se versionan** (están en
`.gitignore`). Después de clonar, copia a mano `agenton-bases-oficiales-2026.docx` en
`docs/datos/` si quieres abrirlas desde la página [HackaPro 2026](hackapro.md). El sitio
construye igual sin ese archivo.

### Variables opcionales del pipeline

Se definen en *Pipelines → (pipeline) → Edit → Variables*.

| Variable | Para qué |
|---|---|
| `SONAR_HOST_URL` | URL de un SonarQube real. Sin ella se usa el servidor efímero |
| `SONAR_TOKEN` | Token de análisis de ese servidor. Márcala como **secreta** |

## Ejecutarlo localmente

Solo se necesitan git y Docker: cada herramienta corre en su contenedor con la misma
versión que el pipeline.

```bash
./scripts/validar-local.sh                     # todas las fases, en orden
./scripts/validar-local.sh --saltar sonarqube  # más rápido
./scripts/validar-local.sh --solo semgrep,api  # fases sueltas (--listar para verlas)
```

Fases: `pre-commit`, `hooks-tests`, `gitleaks`, `semgrep`, `semgrep-demo`, `sonarqube`,
`docs` y `api` (construye `rickmorty-clean` y prueba sus 8 endpoints en un puerto libre).
Reportes y logs en `salida/reportes/`, con un `resumen.md`; el script devuelve error si
alguna fase falla. Cada fase también se puede lanzar sola con
`docker compose --profile seguridad run --rm <servicio>`.

`sonar-analizar.sh` acepta, entre otras, `SONAR_PORT` (si el 9000 está ocupado),
`SONAR_KEEP=1` (deja el servidor arriba para abrir la interfaz con `admin` / `admin`) y
`SONAR_FAIL_ON` (severidades que bloquean). La lista completa está en la cabecera del
script.

## Agentes SAST (`agente-sast-g7/`)

- Los agentes y las *skills* (`/sast`, `/validar-local`, `/replicar-ado`, `/demo`…) están en
  `.github/` de la **raíz del repo**, que es donde GitHub Copilot los carga: abre la raíz
  en VS Code. El agente `orquestador-pruebas` ejecuta el flujo completo; ver
  [Replicar en otra máquina](replicar.md).
- `agente-sast-g7/azure-pipelines.yml` es el pipeline propio del agente (Semgrep →
  normalizar → incidencias). **No está conectado** al pipeline de la raíz: necesita el
  grupo de variables `sast-g7-secrets` con el PAT y un `reportes/validado.json` que hoy
  solo producen los agentes en VS Code. Del agente, el pipeline de la raíz solo reutiliza
  `normalizar_sarif.py` para dejar el reporte de demo en el artefacto.
- `agente-sast-g7/samples/` es código **deliberadamente vulnerable** con secretos falsos.
  Está excluido de gitleaks (`.gitleaks.toml`) y del Semgrep bloqueante
  (`.semgrepignore`); se escanea aparte, sin bloquear.

## Limitaciones

- **SonarQube efímero no guarda historial.** Cada ejecución parte de un servidor vacío: no
  hay tendencia, deuda acumulada ni comparación de "código nuevo". Por eso el bloqueo se
  hace además por severidad (`SONAR_FAIL_ON`). Para historial, usa un servidor real con
  `SONAR_HOST_URL`.
- **SonarQube solo analiza los `.cs`** de `rickmorty-clean/`. El resto del repositorio lo
  cubren Semgrep y gitleaks.
- **La edición Community no analiza ramas ni comenta en los PR.** Aquí el resultado llega
  al PR como comprobación aprobada o fallida del pipeline, no como comentarios.
- **Semgrep descarga sus reglas** del registro público y gitleaks/SonarQube sus imágenes:
  el agente necesita salida a internet o un espejo interno.
- **El hook local se puede saltar** (`git commit --no-verify`); el control real es el
  pipeline.
