#Requires -Version 7.0
<#
.SYNOPSIS
    Ejecuta un comando dentro del contenedor de Azure CLI (servicio "ado" de docker-compose.yml).
    Equivalente en PowerShell 7 (Windows, Linux, macOS) de scripts/ado.sh.

.DESCRIPTION
    No hace falta instalar az: corre en un contenedor con az + git + bash. La sesión de az
    se guarda en ~/.azure (en Windows, %USERPROFILE%\.azure).
    Un PAT, si lo usas, va SOLO en la variable de entorno AZURE_DEVOPS_EXT_PAT de tu sesión
    ($env:AZURE_DEVOPS_EXT_PAT = Read-Host -MaskInput), nunca en archivos.

.EXAMPLE
    ./scripts/ado.ps1 az login --use-device-code
.EXAMPLE
    ./scripts/ado.ps1 ./scripts/ado-bootstrap.sh --org https://dev.azure.com/ORG --project PROY --dry-run
.EXAMPLE
    ./scripts/ado.ps1          # shell interactiva dentro del contenedor
#>
# Sin bloque param: todos los argumentos (incluidos -o, --org, ...) llegan tal cual en $args.

. "$PSScriptRoot/_comun.ps1"

if ($args.Count -gt 0 -and $args[0] -in @('-h', '--help', '-Help', '/?')) {
    Get-Help $PSCommandPath -Detailed
    exit 0
}

$raiz = Get-RaizRepo
Set-Location $raiz
Test-Prerequisito
Initialize-EntornoHost

# Dentro del contenedor el repo está en /repo: se pasa su nombre real (ado-bootstrap.sh y
# ado-pipeline.sh lo usan como nombre del repositorio y del pipeline).
$env:ADO_REPO ??= Split-Path -Leaf $raiz
New-Item -ItemType Directory -Force -Path $env:AZURE_CONFIG_HOST | Out-Null

[string[]]$comando = @($args | ForEach-Object { "$_" })
if ($comando.Count -eq 0) {
    $comando = @('bash')
}
elseif ($comando[0] -like '*.sh') {
    # Un .sh se lanza con bash (en montajes desde NTFS no viaja el bit +x) y con '/'.
    $comando[0] = $comando[0] -replace '\\', '/'
    $comando = @('bash') + $comando
}

$tty = @(Get-ArgumentoTty)   # @() evita que un solo elemento se desenvuelva a texto
& docker compose --profile ado run --rm @tty ado @comando
exit $LASTEXITCODE
