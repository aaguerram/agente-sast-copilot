# Llevar el agente SAST a una máquina sin internet

**Objetivo:** en una máquina **con internet** generar el paquete de imágenes
(`imagenes-sast.tar`) y, en la máquina **sin internet**, trabajar solo con
`docker compose`: nada se descarga ni se instala allí.

> **Qué necesita la máquina sin internet:** Docker (Docker Desktop en Windows), el **código
> del repo** (clon o copia de la carpeta), el archivo `imagenes-sast.tar`, y VS Code con
> GitHub Copilot / acceso a Azure Foundry para los agentes. Nada más.

Las imágenes ya traen dentro todo lo que antes se bajaba al ejecutar:

| Antes se descargaba al ejecutar | Ahora está dentro de la imagen |
|---|---|
| Reglas de Semgrep (`p/default`, `p/csharp`, `p/secrets`) | `agente-pruebas-copilot-semgrep` |
| pre-commit y sus hooks (pre-commit-hooks, gitleaks, PyYAML) | `agente-pruebas-copilot-python` |
| `dotnet-sonarscanner` y paquetes NuGet de los proyectos .NET | `agente-pruebas-copilot-dotnet` |

---

## Parte A — Máquina CON internet (generar el paquete)

Requisitos: Docker corriendo y el repo clonado. Abrir una terminal **dentro de la carpeta
del repo**.

| # | Paso | Windows (PowerShell 7) | Linux / macOS |
|---|---|---|---|
| 1 | (Opcional) Si vas a analizar un proyecto real, clónalo **antes** en `objetivos/` para que sus paquetes NuGet queden en la imagen | `git clone <url> objetivos/mi-proyecto` | igual |
| 2 | Construir, descargar y guardar **todas** las imágenes | `./scripts/imagenes.ps1 exportar` | `./scripts/imagenes.sh exportar` |

Al terminar queda **un archivo** en la carpeta del repo: `imagenes-sast.tar` (unos 6,5 GB, 10
imágenes). Se lleva a la otra máquina por **carpeta compartida o USB**, junto con la carpeta
del repo (incluido `objetivos/` si clonaste un proyecto).

Sin los scripts, los comandos equivalentes son:

```
docker compose --profile "*" build
docker compose --profile "*" pull --ignore-buildable
docker save -o imagenes-sast.tar $(docker compose --profile "*" config --images)
```

---

## Parte B — Máquina SIN internet (cargar y usar)

| # | Paso | Windows (PowerShell 7) | Linux / macOS |
|---|---|---|---|
| 1 | Entrar a la carpeta del repo y copiar allí `imagenes-sast.tar` | `cd <carpeta-del-repo>` | igual |
| 2 | **Cargar** las imágenes y verificar que no falta ninguna | `./scripts/imagenes.ps1 cargar` | `./scripts/imagenes.sh cargar` |
| 3 | Demo: candidatos de la metodología + Semgrep sobre la app vulnerable | `./scripts/agente.ps1 demo` | `./scripts/agente.sh demo` |
| 4 | Lo mismo sobre un proyecto real | `./scripts/agente.ps1 objetivo objetivos/mi-proyecto` | `./scripts/agente.sh objetivo objetivos/mi-proyecto` |
| 5 | Analizadores de seguridad .NET (tercera fuente SARIF) | `./scripts/agente.ps1 dotnet` | `./scripts/agente.sh dotnet` |
| 6 | Todas las fases de validación del repo | `$env:SIN_INTERNET = "1"; ./scripts/validar-local.ps1` | `SIN_INTERNET=1 ./scripts/validar-local.sh` |
| 7 | En VS Code (Copilot Chat) | `/demo`, `/metodologia`, `/sast` | igual |

Sin los scripts: `docker load -i imagenes-sast.tar` y después cualquier servicio, por ejemplo
`docker compose --profile seguridad run --rm semgrep-objetivo` o
`docker compose --profile agentes run --rm py agente-sast-g7/scripts/metodologia.py todo <ruta> --run`.

`./scripts/imagenes.ps1 verificar` (o `.sh`) comprueba en cualquier momento que están las 10
imágenes.

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
- **Analizadores .NET sobre un proyecto nuevo** (`agente dotnet objetivos/<p>`): necesita los
  paquetes NuGet de ese proyecto. Clónalo en `objetivos/` **antes** de la Parte A; si llega
  después, repite la Parte A. Semgrep y la metodología **no** tienen este límite: analizan
  cualquier carpeta.
- **Fase `api` de la validación:** con `SIN_INTERNET=1` usa la imagen `rickmorty-clean-api`
  ya cargada en vez de reconstruirla.
- **No cambies los Dockerfile ni las versiones** (`rev`) de `.pre-commit-config.yaml` en la
  máquina sin internet: reconstruir una imagen necesita red.
- **Replicar en Azure DevOps y crear incidencias** necesitan red hacia `dev.azure.com`.

---

## Qué enviar de vuelta

Para confirmar que la generación fue correcta, enviar la salida de
`./scripts/imagenes.ps1 exportar` (termina con el tamaño y el número de imágenes) y, en la
máquina destino, la de `./scripts/imagenes.ps1 cargar` (debe terminar con «Todas las
imágenes están en esta máquina»).
