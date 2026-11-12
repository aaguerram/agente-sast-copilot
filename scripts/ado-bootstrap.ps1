#Requires -Version 7.0
<#
.SYNOPSIS
    Sube este repositorio a un proyecto de Azure DevOps y deja el pipeline corriendo en cada
    pull request a main. Equivalente en PowerShell 7 de scripts/ado-bootstrap.sh.

.DESCRIPTION
    Ejecuta scripts/ado-bootstrap.sh dentro del contenedor de Azure CLI (scripts/ado.ps1),
    así que la lógica es la misma en Windows, Linux y macOS. Es idempotente.
    Antes: ./scripts/ado.ps1 az login --use-device-code   (o $env:AZURE_DEVOPS_EXT_PAT).
    Sube la rama main tal como está COMMITEADA.

.PARAMETER Org
    URL de la organización: https://dev.azure.com/MI_ORG (o $env:ADO_ORG_URL).
.PARAMETER Project
    Proyecto existente (o $env:ADO_PROJECT).
.PARAMETER Repo
    Nombre del repositorio a crear. Por defecto, el nombre de la carpeta del repo.
.PARAMETER Pipeline
    Nombre del pipeline. Por defecto, <repo>-seguridad.
.PARAMETER DryRun
    Solo consultas (GET): muestra qué crearía sin crear ni subir nada.

.EXAMPLE
    ./scripts/ado-bootstrap.ps1 -Org https://dev.azure.com/MI_ORG -Project MI_PROYECTO -DryRun
.EXAMPLE
    ./scripts/ado-bootstrap.ps1 -Org https://dev.azure.com/MI_ORG -Project MI_PROYECTO
#>
[CmdletBinding()]
param(
    [string]$Org,
    [string]$Project,
    [string]$Repo,
    [string]$Pipeline,
    [switch]$DryRun,
    [switch]$Help
)

$argumentos = [System.Collections.Generic.List[string]]::new()
if ($Help) { $argumentos.Add('--help') }
if ($Org) { $argumentos.AddRange([string[]]@('--org', $Org)) }
if ($Project) { $argumentos.AddRange([string[]]@('--project', $Project)) }
if ($Repo) { $argumentos.AddRange([string[]]@('--repo', $Repo)) }
if ($Pipeline) { $argumentos.AddRange([string[]]@('--pipeline', $Pipeline)) }
if ($DryRun) { $argumentos.Add('--dry-run') }

& (Join-Path $PSScriptRoot 'ado.ps1') bash scripts/ado-bootstrap.sh @argumentos
exit $LASTEXITCODE
