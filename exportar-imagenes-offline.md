# Llevar el agente SAST a una máquina sin internet

**Objetivo:** en una máquina **con internet** generar el paquete de imágenes
(`imagenes-sast.tar`) y, en la máquina **sin internet**, trabajar solo con
`docker compose`: allí nada se descarga ni se instala.

## Qué se lleva a la máquina sin internet

| # | Qué | De dónde sale | Tamaño |
|---|---|---|---|
| 1 | La **carpeta del repo completa**, con su carpeta oculta `.git` | `git clone` en la máquina con internet (Parte A) | unos 25 MB |
| 2 | `imagenes-sast.tar` (las 10 imágenes) | `imagenes exportar` (Parte A) | unos 6,5 GB |
| 3 | El **código** de los proyectos a analizar | Se copia a `objetivos/` en la máquina destino; no hace falta compilarlo | el del proyecto |

El repo y el `.tar` deben salir **del mismo clon**: las imágenes llevan dentro los hooks y
paquetes de esa versión del código.

Las imágenes ya traen dentro todo lo que antes se bajaba al ejecutar:

| Antes se descargaba al ejecutar | Ahora está dentro de la imagen |
|---|---|
| Reglas de Semgrep (`p/default`, `p/csharp`, `p/secrets`) | `agente-pruebas-copilot-semgrep` |
| pre-commit y sus hooks (pre-commit-hooks, gitleaks, PyYAML) | `agente-pruebas-copilot-python` |
| `dotnet-sonarscanner` y paquetes NuGet de los proyectos .NET | `agente-pruebas-copilot-dotnet` |

## Qué debe tener YA instalado la máquina sin internet

Esto **no viaja en el paquete** y allí no se puede descargar: hay que comprobarlo antes de ir
(o llevar el instalador en el mismo USB).

| Requisito | Para qué | Si falta |
|---|---|---|
| **Docker** con `docker compose` (Windows: Docker Desktop con WSL2, en modo contenedores Linux) | Todo | Llevar el instalador; sin Docker no funciona nada |
| **PowerShell 7** (`pwsh`), solo en Windows | Los scripts `.ps1` exigen la versión 7; el Windows PowerShell 5.1 que trae Windows no los ejecuta | Llevar el instalador `.msi` de PowerShell 7, o usar los «comandos sin scripts» (funcionan en 5.1) |
| **Git** | Solo el paso 7 (`validar-local`: pre-commit y gitleaks leen el historial) | Los pasos 1 a 6 y 8 funcionan sin Git |
| **VS Code + GitHub Copilot** con sesión iniciada y acceso de red a Copilot / Azure Foundry | Los agentes del chat (`/demo`, `/metodologia`, `/sast`) | Sin eso funcionan los pasos de terminal, no el chat |
| **15 GB libres** en disco | 6,5 GB del `.tar` + unos 6,6 GB de las imágenes ya cargadas | El `.tar` se puede borrar después de cargarlo |

---

## Parte A — Máquina CON internet (generar el paquete)

Requisitos: Docker corriendo y Git. La máquina debe ser **del mismo tipo de procesador** que
la de destino (ver paso 1).

| # | Paso | Windows (PowerShell 7) | Linux / macOS |
|---|---|---|---|
| 1 | Anotar la arquitectura (debe ser **igual** en la máquina destino; lo habitual es `linux/amd64`) | `docker version --format "{{.Server.Os}}/{{.Server.Arch}}"` | igual |
| 2 | Clonar el repo y entrar a la carpeta (no usar «Descargar ZIP»: no trae `.git`) | `git clone <url-del-repo>` y `cd <carpeta-del-repo>` | igual |
| 3 | Construir, descargar y guardar **todas** las imágenes | `./scripts/imagenes.ps1 exportar` | `./scripts/imagenes.sh exportar` |
| 4 | Anotar la huella del archivo, para comprobar la copia | `Get-FileHash imagenes-sast.tar -Algorithm SHA256` | `sha256sum imagenes-sast.tar` (macOS: `shasum -a 256`) |
| 5 | Copiar al USB o carpeta compartida la **carpeta del repo** y `imagenes-sast.tar` | Explorador de archivos | `tar czf repo.tgz <carpeta-del-repo>` conserva los permisos |

El paso 3 termina con `Listo: imagenes-sast.tar (… GB, 10 imágenes)`.

> **El USB debe estar en exFAT o NTFS.** FAT32 no admite archivos de más de 4 GB y el `.tar`
> pesa unos 6,5 GB: la copia falla con «archivo demasiado grande».

Sin los scripts, los comandos equivalentes al paso 3 son:

```
docker compose --profile "*" build
docker compose --profile "*" pull --ignore-buildable
docker save -o imagenes-sast.tar $(docker compose --profile "*" config --images)
```

---

## Parte B — Máquina SIN internet (cargar y usar)

Copiar la carpeta del repo al **disco local** (no trabajar desde el USB); puede tener
cualquier nombre. Abrir una terminal dentro de ella.

| # | Paso | Windows (PowerShell 7) | Linux / macOS |
|---|---|---|---|
| 1 | Entrar a la carpeta del repo y copiar allí `imagenes-sast.tar` | `cd <carpeta-del-repo>` | igual |
| 2 | Comprobar la arquitectura: debe dar lo mismo que en la Parte A | `docker version --format "{{.Server.Os}}/{{.Server.Arch}}"` | igual |
| 3 | Comprobar la huella: debe ser idéntica a la anotada | `Get-FileHash imagenes-sast.tar -Algorithm SHA256` | `sha256sum imagenes-sast.tar` |
| 4 | **Cargar** las imágenes y verificar que no falta ninguna | `./scripts/imagenes.ps1 cargar` | `./scripts/imagenes.sh cargar` |
| 5 | Demo: candidatos de la metodología + Semgrep sobre la app vulnerable, **sin compilar** | `./scripts/agente.ps1 demo --sin-dotnet` | `./scripts/agente.sh demo --sin-dotnet` |
| 6 | Lo mismo sobre un proyecto real (basta copiar su código a `objetivos/`) | `./scripts/agente.ps1 objetivo objetivos/mi-proyecto --sin-dotnet` | `./scripts/agente.sh objetivo objetivos/mi-proyecto --sin-dotnet` |
| 7 | Todas las fases de validación del repo (necesita Git y la carpeta `.git`) | `$env:SIN_INTERNET = "1"; ./scripts/validar-local.ps1` | `SIN_INTERNET=1 ./scripts/validar-local.sh` |
| 8 | En VS Code (Copilot Chat) | `/demo`, `/metodologia`, `/sast` | igual |

El paso 4 debe terminar con «Todas las imágenes están en esta máquina: se puede trabajar sin
internet». Para no duplicar el archivo en disco se puede cargar directo desde el USB:
`./scripts/imagenes.ps1 cargar D:\imagenes-sast.tar` (o `.sh` con su ruta).
`./scripts/imagenes.ps1 verificar` comprueba en cualquier momento que están las 10 imágenes.

`--sin-dotnet` omite los analizadores de seguridad .NET, el **único paso que compila** el
proyecto y que necesita sus paquetes NuGet (no disponibles sin internet). El análisis se hace
solo con el código fuente: metodología, Semgrep y los agentes de Copilot. Si defines
`SIN_INTERNET=1` en la sesión, `demo` y `objetivo` omiten ese paso solos.

### Comandos sin scripts

Sirven en cualquier terminal, también en Windows PowerShell 5.1 (sin PowerShell 7).
Equivalen a los pasos 4 a 6:

```
docker load -i imagenes-sast.tar
docker compose --profile "*" config --images
docker images
docker compose --profile agentes run --rm py agente-sast-g7/scripts/metodologia.py todo objetivos/mi-proyecto --dir salida/reportes/metodologia
```

Las 10 imágenes de la segunda orden deben aparecer en la lista de la tercera. Después,
Semgrep sobre el mismo proyecto:

| Terminal | Comando |
|---|---|
| PowerShell | `$env:OBJETIVO = "objetivos/mi-proyecto"; docker compose --profile seguridad run --rm semgrep-objetivo` |
| Linux / macOS | `OBJETIVO=objetivos/mi-proyecto docker compose --profile seguridad run --rm semgrep-objetivo` |

Los reportes quedan en `salida/reportes/`.

---

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| El `.tar` no se copia al USB («archivo demasiado grande») | USB en FAT32 (máximo 4 GB por archivo) | Formatear el USB en exFAT o NTFS, o usar una carpeta compartida |
| La huella SHA-256 no coincide, o `docker load` da error | Copia incompleta o dañada | Volver a copiar el `.tar` |
| `FALTA <imagen>` después de cargar | El `.tar` es de otra versión del repo o está incompleto | Repetir la Parte A con el mismo clon que se lleva |
| `exec format error` o aviso de `platform` al ejecutar | El paquete se hizo en otra arquitectura (ARM frente a x64) | Repetir la Parte A en una máquina con la misma arquitectura |
| Docker intenta descargar o construir (`pull access denied`, `failed to resolve`, espera de red) | Falta una imagen o se modificó un Dockerfile | `imagenes verificar`; no cambiar los Dockerfile en esta máquina |
| El `.ps1` no arranca: «#requires … PowerShell 7.0» | Se abrió Windows PowerShell 5.1 | Abrir `pwsh` (PowerShell 7) o usar los comandos sin scripts |
| El `.ps1` no arranca: «la ejecución de scripts está deshabilitada» | Directiva de ejecución de PowerShell | `pwsh -ExecutionPolicy Bypass -File ./scripts/imagenes.ps1 cargar` |
| `Permission denied` al ejecutar un `.sh` | La copia por USB quitó el permiso de ejecución | `bash scripts/imagenes.sh cargar` (anteponer `bash`), o `chmod +x scripts/*.sh` |
| `validar-local`: «no es un repositorio git» | Se copió la carpeta sin `.git` o falta Git | Copiar el clon completo; `demo` y `objetivo` no lo necesitan |

---

## Las 10 imágenes del paquete

| Imagen | Tipo | Función |
|---|---|---|
| `agente-pruebas-copilot-semgrep` | compilada | Semgrep CE 1.185.0 **con las reglas del registro dentro** (gate, demo y proyecto objetivo) |
| `agente-pruebas-copilot-python` | compilada | Python 3.12 + git + pre-commit **con los hooks instalados**; scripts de los agentes (metodología, normalizar SARIF, incidencias) |
| `agente-pruebas-copilot-dotnet` | compilada | SDK .NET 10 + `dotnet-sonarscanner` + **caché de NuGet** (analizadores .NET y SonarQube) |
| `agente-pruebas-copilot-sonarqube` | compilada | Lanza el análisis de SonarQube (cliente Docker + curl + python) |
| `sonarqube:community` | descargada | Servidor SonarQube efímero |
| `ghcr.io/gitleaks/gitleaks:v8.30.1` | descargada | Detección de secretos en el historial |
| `agente-pruebas-copilot-docs` | compilada | Sitio MkDocs (en vivo y generación estática) |
| `plantuml/plantuml-server:jetty` | descargada | Render de diagramas de la documentación |
| `rickmorty-clean-api` | compilada | API de ejemplo (fase `api` de la validación) |
| `agente-pruebas-copilot-ado` | compilada | Azure CLI para replicar en otro Azure DevOps (esa acción sí necesita red hacia Azure DevOps) |

---

## Límites sin internet

- **Misma arquitectura en las dos máquinas.** Las imágenes se construyen para el procesador
  de la máquina que exporta: genera el paquete en un equipo del mismo tipo que el destino
  (lo habitual, ambos Windows/Linux x64). Un paquete hecho en ARM (Mac con Apple Silicon,
  equipos ARM64) no sirve en un equipo x64, y al revés.
- **Reglas de Semgrep y hooks de pre-commit** son los del día en que se construyó la imagen.
  Para actualizarlos, repetir la Parte A (`docker compose --profile "*" build --no-cache semgrep`
  fuerza a bajar las reglas de nuevo).
- **Analizadores de seguridad .NET: no se usan sin internet.** Compilan el proyecto y
  necesitan sus paquetes NuGet; por eso los pasos de la Parte B llevan `--sin-dotnet`. Semgrep
  y la metodología **no** compilan: analizan cualquier carpeta de código. (La app vulnerable de
  muestra sí trae sus paquetes en la imagen: `./scripts/agente.sh dotnet` funciona sobre ella.)
- **Fase `api` de la validación:** con `SIN_INTERNET=1` usa la imagen `rickmorty-clean-api`
  ya cargada en vez de reconstruirla.
- **No cambies los Dockerfile ni las versiones** (`rev`) de `.pre-commit-config.yaml` en la
  máquina sin internet: reconstruir una imagen necesita red.
- **Replicar en Azure DevOps y crear incidencias** necesitan red hacia `dev.azure.com`.
- **Los agentes de Copilot Chat** necesitan la conexión de VS Code con GitHub Copilot / Azure
  Foundry. Los pasos de terminal (4 a 7) funcionan sin ninguna red.

---

## Qué enviar de vuelta

Para confirmar que todo salió bien, enviar:

1. La salida de `./scripts/imagenes.ps1 exportar` (termina con el tamaño y el número de
   imágenes) y la huella SHA-256 del archivo.
2. En la máquina destino, la salida de `./scripts/imagenes.ps1 cargar` (debe terminar con
   «Todas las imágenes están en esta máquina») y la de `demo --sin-dotnet`.
