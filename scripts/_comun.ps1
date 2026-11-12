#Requires -Version 7.0
# Funciones comunes de los scripts .ps1 del repo. Se carga con:
#   . "$PSScriptRoot/_comun.ps1"
# Detecta el entorno del host (Windows, Linux o macOS) y prepara las variables que usa
# docker-compose.yml, igual que hacen los .sh en Linux. No instala nada.

Set-StrictMode -Version 3.0

function Exit-ConError {
    param([Parameter(Mandatory)][string]$Mensaje, [int]$Codigo = 1)
    [Console]::Error.WriteLine($Mensaje)
    exit $Codigo
}

function Get-RaizRepo {
    (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}

# Ruta en el formato que acepta docker compose en cualquier SO (C:\x\y -> C:/x/y).
function ConvertTo-RutaDocker {
    param([Parameter(Mandatory)][string]$Ruta)
    $Ruta -replace '\\', '/'
}

function Test-Prerequisito {
    param([switch]$Git)
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Exit-ConError 'ERROR: falta Docker (en Windows: Docker Desktop con backend WSL2).'
    }
    & docker compose version *> $null
    if ($LASTEXITCODE -ne 0) { Exit-ConError "ERROR: falta el plugin 'docker compose'." }
    & docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        Exit-ConError 'ERROR: Docker no responde (¿Docker Desktop abierto? En Linux, ¿tu usuario está en el grupo docker?).'
    }
    if ($Git) {
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            Exit-ConError 'ERROR: falta git (en Windows: Git for Windows).'
        }
        & git rev-parse --is-inside-work-tree *> $null
        if ($LASTEXITCODE -ne 0) {
            Exit-ConError 'ERROR: esta carpeta no es un repositorio git (pre-commit y gitleaks lo necesitan). Clónala con git.'
        }
    }
}

# Variables de docker-compose.yml que dependen de la máquina. Respeta las que ya existan.
function Initialize-EntornoHost {
    $perfil = [Environment]::GetFolderPath('UserProfile')
    if ($IsWindows -or $IsMacOS) {
        # Docker Desktop: los archivos montados no tienen dueño Unix (1000:1000 escribe sin
        # problema) y el socket de Docker dentro de la VM solo lo usa root.
        $env:UID ??= '1000'
        $env:GID ??= '1000'
        $env:DOCKER_GID ??= '0'
        $env:SONAR_RUN_USER ??= '0:0'
    }
    else {
        $env:UID ??= (& id -u)
        $env:GID ??= (& id -g)
        if (-not $env:DOCKER_GID) {
            $gid = & stat -c '%g' /var/run/docker.sock 2>$null
            $env:DOCKER_GID = if ($LASTEXITCODE -eq 0 -and $gid) { $gid } else { '0' }
        }
    }
    $env:PRE_COMMIT_CACHE ??= ConvertTo-RutaDocker (Join-Path $perfil '.cache/agente-pruebas-pre-commit')
    $env:AZURE_CONFIG_HOST ??= ConvertTo-RutaDocker (Join-Path $perfil '.azure')
}

# docker compose run necesita -T cuando no hay terminal interactiva (VS Code tasks, CI, tuberías).
function Get-ArgumentoTty {
    if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected) { @('-T') } else { @() }
}
