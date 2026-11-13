#Requires -Version 7.0
<#
.SYNOPSIS
    Lleva TODAS las imágenes del repo a una máquina sin internet. Equivalente en
    PowerShell 7 de scripts/imagenes.sh. Guía paso a paso: exportar-imagenes-offline.md.

.DESCRIPTION
    Las imágenes ya traen las reglas de Semgrep, los hooks de pre-commit, el scanner de
    SonarQube y los paquetes NuGet: en la máquina destino no se descarga nada.
    El archivo por defecto es imagenes-sast.tar en la raíz del repo (no se versiona).

.PARAMETER Comando
    exportar   máquina CON internet: construye, descarga y guarda las imágenes en el archivo.
    cargar     máquina SIN internet: docker load del archivo y verificación.
    verificar  comprueba que no falta ninguna imagen.
    listar     imágenes que usa el repo.

.EXAMPLE
    ./scripts/imagenes.ps1 exportar
.EXAMPLE
    ./scripts/imagenes.ps1 cargar D:\imagenes-sast.tar
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)][string]$Comando = 'ayuda',
    [Parameter(Position = 1)][string]$Archivo = 'imagenes-sast.tar'
)

. "$PSScriptRoot/_comun.ps1"
Set-Location (Get-RaizRepo)

function Get-Imagenes {
    $lista = @(& docker compose --profile '*' config --images | Where-Object { $_ } | Sort-Object -Unique)
    if ($LASTEXITCODE -ne 0 -or $lista.Count -eq 0) { Exit-ConError 'ERROR: no se pudo leer docker-compose.yml.' }
    $lista
}

function Test-Imagenes {
    param([switch]$Silencioso)
    $faltan = 0
    foreach ($img in Get-Imagenes) {
        & docker image inspect $img *> $null
        if ($LASTEXITCODE -eq 0) { if (-not $Silencioso) { "   OK     $img" } }
        else { "   FALTA  $img"; $faltan++ }
    }
    if ($faltan -gt 0) { Exit-ConError "ERROR: faltan $faltan imagen(es)." }
    if (-not $Silencioso) { 'Todas las imágenes están en esta máquina: se puede trabajar sin internet.' }
}

switch ($Comando) {
    { $_ -in 'ayuda', 'help', '-h', '--help' } { Get-Help $PSCommandPath -Detailed; exit 0 }
    'listar' { Test-Prerequisito; Initialize-EntornoHost; Get-Imagenes }
    'verificar' { Test-Prerequisito; Initialize-EntornoHost; Test-Imagenes }
    'exportar' {
        Test-Prerequisito; Initialize-EntornoHost
        '>> 1/3 Construyendo las imágenes propias (tools/ y rickmorty-clean)'
        & docker compose --profile '*' build
        if ($LASTEXITCODE -ne 0) { Exit-ConError 'ERROR: falló la construcción de las imágenes.' }
        '>> 2/3 Descargando las imágenes de registro'
        & docker compose --profile '*' pull --ignore-buildable
        if ($LASTEXITCODE -ne 0) { Exit-ConError 'ERROR: falló la descarga de las imágenes.' }
        ">> 3/3 Guardando en $Archivo"
        Test-Imagenes -Silencioso
        $lista = @(Get-Imagenes)
        & docker save -o $Archivo @lista
        if ($LASTEXITCODE -ne 0) { Exit-ConError 'ERROR: falló docker save.' }
        $gb = [math]::Round((Get-Item $Archivo).Length / 1GB, 2)
        "Listo: $Archivo ($gb GB, $($lista.Count) imágenes). Cópialo junto con el repo a la máquina sin internet y allí: ./scripts/imagenes.ps1 cargar"
    }
    'cargar' {
        Test-Prerequisito; Initialize-EntornoHost
        if (-not (Test-Path $Archivo)) { Exit-ConError "ERROR: no existe $Archivo" }
        & docker load -i $Archivo
        if ($LASTEXITCODE -ne 0) { Exit-ConError 'ERROR: falló docker load.' }
        Test-Imagenes
    }
    default { Exit-ConError "Subcomando desconocido: $Comando (usa: exportar, cargar, verificar, listar)." }
}
