# Exportar las imágenes del agente SAST para la red interna (sin internet)

**Objetivo:** en una máquina **con internet** generar el paquete de imágenes
(`imagenes-sast.tar`) para que, en un entorno **sin internet**, cualquier persona de la red
interna pueda levantar el agente.

> **Nota:** este instructivo cubre **solo las imágenes**. El **código del repo** debe estar
> disponible en el destino por su propia vía (clon del repositorio o la copia ya desplegada
> en la red interna); el `docker compose` lo monta en tiempo de ejecución.

---

## Parte A — Máquina CON internet (generar el paquete de imágenes)

Requisitos: Windows + **Docker Desktop corriendo**. Abrir **PowerShell** y situarse
**dentro de la carpeta del repo** antes de empezar.

| # | Paso | Comando (PowerShell) |
|---|---|---|
| 0 | Dejar registro de toda la sesión (opcional, recomendado) | `Start-Transcript -Path .\salida-export.txt` |
| 1 | Verificar que Docker responde | `docker version` |
| 2 | **Compilar** las imágenes locales (docs, sonarqube, ado) | `docker compose --profile tools --profile seguridad --profile ado build` |
| 3 | **Descargar** las imágenes de registro (semgrep, python, gitleaks, plantuml) | `docker compose --profile seguridad --profile agentes pull --ignore-buildable` |
| 4 | Ver la lista de imágenes que se exportarán (deben ser 8) | `docker compose --profile tools --profile seguridad --profile agentes --profile ado config --images \| Sort-Object -Unique` |
| 5 | **Exportar** todas las imágenes a un solo archivo | `docker save -o imagenes-sast.tar $(docker compose --profile tools --profile seguridad --profile agentes --profile ado config --images \| Sort-Object -Unique)` |
| 6 | Ver el tamaño del paquete | `Get-ChildItem imagenes-sast.tar \| Select-Object Name, @{n='GB';e={[math]::Round($_.Length/1GB,2)}}` |
| 7 | Cerrar el registro de la sesión | `Stop-Transcript` |

Al terminar queda **un archivo** en la carpeta del repo:

- `imagenes-sast.tar` — las 8 imágenes Docker (varios GB).

> Este archivo se lleva a la red interna por **carpeta compartida o USB** (es grande, no por
> correo). El correo con este instructivo es solo la guía de pasos.

---

## Parte B — Máquina SIN internet (red interna, usar las imágenes)

Requisitos: Docker Desktop corriendo, el **código del repo ya presente** en la máquina, y
copiar allí `imagenes-sast.tar`.

| # | Paso | Comando (PowerShell) |
|---|---|---|
| 1 | **Cargar** las imágenes (no baja nada de internet) | `docker load -i imagenes-sast.tar` |
| 2 | Confirmar que quedaron cargadas | `docker images` |
| 3 | Entrar a la carpeta del repo | `cd <carpeta-del-repo>` |
| 4 | Ejecutar un control, p. ej. SAST del repo | `docker compose --profile seguridad run --rm semgrep` |
| 5 | Agente sobre un proyecto objetivo | `docker compose --profile agentes run --rm py agente-sast-g7/scripts/metodologia.py todo <ruta> --run` |

Como las imágenes ya están cargadas y el código está en disco, **no hace falta internet**.

---

## Las 8 imágenes del paquete

| Imagen | Tipo | Función |
|---|---|---|
| `semgrep/semgrep:1.185.0` | descargada | SAST (gate del repo, demo y proyecto objetivo) |
| `python:3.12` | descargada | Scripts de agente (metodología, normalizar SARIF, incidencias) y pre-commit |
| `ghcr.io/gitleaks/gitleaks:v8.30.1` | descargada | Detección de secretos |
| `plantuml/plantuml-server:jetty` | descargada | Render de diagramas de la documentación |
| `agente-pruebas-copilot-sonarqube` | compilada | SonarQube efímero + SDK .NET |
| `agente-pruebas-copilot-docs` | compilada | Sitio MkDocs en vivo |
| `agente-pruebas-copilot-docs-build` | compilada | Genera el sitio estático |
| `agente-pruebas-copilot-ado` | compilada | Azure CLI para replicar en otro Azure DevOps |

---

## Qué enviar de vuelta

Para confirmar que la generación fue correcta, enviar de vuelta:

1. El archivo de registro **`salida-export.txt`** (la consola de todos los pasos).
2. La salida del **paso 4** (lista de 8 imágenes) y del **paso 6** (tamaño).

El paquete `imagenes-sast.tar` se distribuye por la **red interna** (carpeta compartida /
USB), no por correo.
