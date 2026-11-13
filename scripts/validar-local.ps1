#Requires -Version 7.0
<#
.SYNOPSIS
    Ejecuta en local TODAS las fases de prueba del repositorio, en contenedores
    (docker compose). Equivalente en PowerShell 7 (Windows, Linux, macOS) de
    scripts/validar-local.sh: mismas fases, mismos reportes y mismos códigos de salida.

.DESCRIPTION
    Solo necesita git, Docker (Docker Desktop en Windows/macOS) y PowerShell 7.
    No instala nada en la máquina.

    Fases (mismo orden y versiones que azure-pipelines.yml, más docs y la API):
      pre-commit    hooks de .pre-commit-config.yaml (incluye gitleaks y los hooks .NET)
      hooks-tests   pruebas de los hooks .NET propios (tools/pre-commit-hooks/tests)
      gitleaks      secretos en todo el historial de git
      semgrep       Semgrep CE bloqueante (registro + reglas de .semgrep/)
      semgrep-demo  reporte con hallazgos sobre la muestra vulnerable + normalización
      metodologia   pruebas del script de la metodología SAST + candidatos de la app vulnerable
      sonarqube     SonarQube Community efímero sobre rickmorty-clean
      docs          sitio MkDocs en modo estricto (salida/sitio.zip)
      api           build de la imagen de rickmorty-clean y prueba de humo de sus endpoints

    Reportes: salida/reportes/ (SARIF, JSON normalizado, logs/<fase>.log, resumen.md).
    Salida: 0 si todas las fases pasan, 1 si alguna falla.
    Variables opcionales: COMPOSE_PROJECT_NAME, SONAR_PORT (def. 9100), API_PORT_SMOKE (def. 18080),
    SIN_INTERNET=1 (máquina sin internet: la fase api usa la imagen ya cargada, no la reconstruye).

.PARAMETER Solo
    Ejecuta solo estas fases (lista separada por comas).
.PARAMETER Saltar
    Ejecuta todas menos estas fases.
.PARAMETER Listar
    Muestra las fases y termina.

.EXAMPLE
    ./scripts/validar-local.ps1
.EXAMPLE
    ./scripts/validar-local.ps1 -Saltar sonarqube
.EXAMPLE
    ./scripts/validar-local.ps1 -Solo semgrep,api
#>
[CmdletBinding()]
param(
    [string[]]$Solo = @(),
    [string[]]$Saltar = @(),
    [switch]$Listar
)

. "$PSScriptRoot/_comun.ps1"

$Todas = @('pre-commit', 'hooks-tests', 'gitleaks', 'semgrep', 'semgrep-demo', 'metodologia', 'sonarqube', 'docs', 'api')
if ($Listar) { $Todas; exit 0 }

# Acepta "-Solo a,b" y "-Solo 'a,b'".
$Solo = @($Solo | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$Saltar = @($Saltar | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
foreach ($f in $Solo + $Saltar) {
    if ($f -notin $Todas) { Exit-ConError "Fase desconocida: $f (usa -Listar)." }
}

$Raiz = Get-RaizRepo
Set-Location $Raiz
Test-Prerequisito -Git
Initialize-EntornoHost

$Reportes = Join-Path $Raiz 'salida/reportes'
$Logs = Join-Path $Reportes 'logs'
# Se crean ANTES de montarlos (si los crea Docker, en Linux quedan de root).
New-Item -ItemType Directory -Force -Path $Reportes, $Logs | Out-Null
$Proyecto = if ($env:COMPOSE_PROJECT_NAME) { $env:COMPOSE_PROJECT_NAME } else { 'agente-pruebas-copilot' }

# ------------------------------------------------------------ utilidades
function Invoke-Dc {
    & docker compose -p $Proyecto @args
    if ($LASTEXITCODE -ne 0) { throw "docker compose $($args -join ' ') terminó con código $LASTEXITCODE" }
}

# Construye la imagen de un servicio solo si falta: con las imágenes ya cargadas
# (docker load) no se toca la red. Tras cambiar un Dockerfile: docker compose --profile "*" build
function Confirm-Imagen {
    param([Parameter(Mandatory)][string]$Imagen, [Parameter(Mandatory)][string]$Servicio)
    & docker image inspect $Imagen *> $null
    if ($LASTEXITCODE -ne 0) { Invoke-Dc --profile '*' build -q $Servicio }
}

function Get-PuertoLibre {
    $p = if ($env:API_PORT_SMOKE) { [int]$env:API_PORT_SMOKE } else { 18080 }
    # Puertos ya publicados por Docker (en Docker Desktop no siempre se ven con un connect local).
    $publicados = @(& docker ps --format '{{.Ports}}' 2>$null |
            Select-String -AllMatches -Pattern ':(\d+)->' |
            ForEach-Object { $_.Matches } | ForEach-Object { [int]$_.Groups[1].Value })
    while ($true) {
        if ($p -in $publicados) { $p++; continue }
        $cliente = [System.Net.Sockets.TcpClient]::new()
        try {
            $ocupado = $cliente.ConnectAsync('127.0.0.1', $p).Wait(300) -and $cliente.Connected
        }
        catch { $ocupado = $false }
        finally { $cliente.Dispose() }
        if (-not $ocupado) { return $p }
        $p++
    }
}

# ------------------------------------------------------------ fases
$Fases = [ordered]@{
    'pre-commit'   = { Invoke-Dc --profile seguridad run --rm -T pre-commit }
    'hooks-tests'  = { Invoke-Dc --profile seguridad run --rm -T pre-commit-hooks-tests }
    'gitleaks'     = { Invoke-Dc --profile seguridad run --rm -T gitleaks }
    'semgrep'      = { Invoke-Dc --profile seguridad run --rm -T semgrep }
    'semgrep-demo' = {
        $json = Join-Path $Reportes 'muestras-normalizado.json'
        Remove-Item -Force -ErrorAction SilentlyContinue $json
        Invoke-Dc --profile seguridad run --rm -T semgrep-demo
        $n = if (Test-Path $json) { @(Select-String -Path $json -Pattern '"regla"').Count } else { 0 }
        ">> Hallazgos normalizados en la muestra: $n"
        if ($n -le 0) { throw 'La muestra vulnerable no produjo hallazgos normalizados.' }
    }
    'metodologia'  = {
        Invoke-Dc --profile agentes run --rm -T py agente-sast-g7/scripts/tests/test_metodologia.py
        Invoke-Dc --profile agentes run --rm -T py agente-sast-g7/scripts/tests/test_kb.py
        Invoke-Dc --profile agentes run --rm -T py agente-sast-g7/scripts/metodologia.py todo `
            agente-sast-g7/samples/app-vulnerable --dir salida/reportes/metodologia
    }
    'sonarqube'    = {
        # El SDK con el scanner y la caché de NuGet lo lanza sonar-analizar.sh como contenedor hermano.
        Confirm-Imagen agente-pruebas-copilot-dotnet dotnet-objetivo
        Invoke-Dc --profile seguridad run --rm -T sonarqube
    }
    'docs'         = {
        $habia = & docker compose -p $Proyecto ps -q plantuml 2>$null
        try { Invoke-Dc --profile tools run --rm -T docs-build }
        finally {
            # Si plantuml lo levantó esta corrida, se baja; si ya estaba (sitio en vivo), se deja.
            if (-not $habia) { & docker compose -p $Proyecto rm -sf plantuml *> $null }
        }
    }
    'api'          = {
        $proy = "$Proyecto-api-smoke"
        $puerto = Get-PuertoLibre
        $api = @('compose', '-p', $proy, '-f', 'rickmorty-clean/docker-compose.yml')
        $env:API_PORT = "$puerto"
        $fallas = 0
        try {
            $construir = @('--build')
            if ($env:SIN_INTERNET -eq '1') {
                $construir = @()
                '>> SIN_INTERNET=1: se usa la imagen rickmorty-clean-api ya cargada (no se reconstruye)'
            }
            ">> Levantando rickmorty-clean en el puerto $puerto (proyecto $proy)"
            & docker @api up -d @construir --wait --wait-timeout 180
            if ($LASTEXITCODE -ne 0) {
                $fallas++
                if ($construir.Count -gt 0) { '   Si esta máquina no tiene internet, repite con $env:SIN_INTERNET = "1" (usa la imagen ya cargada).' }
            }
            else {
                # La prueba corre en UN contenedor de la misma red: no depende de curl en el host.
                Confirm-Imagen agente-pruebas-copilot-python py
                $humo = ConvertTo-RutaDocker (Join-Path $Raiz 'scripts/api_humo.py')
                & docker run --rm --network "${proy}_default" -v "${humo}:/api_humo.py:ro" `
                    agente-pruebas-copilot-python python /api_humo.py http://api:8080
                if ($LASTEXITCODE -ne 0) { $fallas++ }
            }
            if ($fallas -gt 0) { & docker @api logs --tail 40 2>&1 | ForEach-Object { "   $_" } }
        }
        finally {
            & docker @api down -v *> $null
            Remove-Item Env:API_PORT -ErrorAction SilentlyContinue
        }
        if ($fallas -gt 0) { throw "$fallas comprobación(es) de la API fallaron." }
    }
}

# ------------------------------------------------------------ ejecución
$Resultado = @{}; $Duracion = @{}; $Fallas = 0
foreach ($f in $Todas) {
    if (($Solo.Count -gt 0 -and $f -notin $Solo) -or $f -in $Saltar) { $Resultado[$f] = 'omitida'; continue }
    ''
    "==================== $f"
    $log = Join-Path $Logs "$f.log"
    $reloj = [System.Diagnostics.Stopwatch]::StartNew()
    $ok = $true
    try {
        & $Fases[$f] 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $log
    }
    catch {
        "ERROR: $($_.Exception.Message)" | Tee-Object -FilePath $log -Append
        $ok = $false
    }
    $Duracion[$f] = [int]$reloj.Elapsed.TotalSeconds
    if ($ok) { $Resultado[$f] = 'OK' } else { $Resultado[$f] = 'FALLA'; $Fallas++ }
}

# ------------------------------------------------------------ resumen
$commit = (& git rev-parse --short HEAD 2>$null) ?? 'sin-commit'
& git diff --quiet 2>$null
$sucio = if ($LASTEXITCODE -ne 0) { ' (con cambios sin commit)' } else { '' }
$md = [System.Collections.Generic.List[string]]::new()
$md.Add("# Validación local — $(Get-Date -Format 'yyyy-MM-dd HH:mm')")
$md.Add('')
$md.Add("Commit: ``$commit``$sucio · Sistema: $([System.Runtime.InteropServices.RuntimeInformation]::OSDescription) · PowerShell $($PSVersionTable.PSVersion)")
$md.Add('')
$md.Add('| Fase | Resultado | Duración | Log |')
$md.Add('|---|---|---|---|')
foreach ($f in $Todas) {
    $d = if ($Duracion.ContainsKey($f)) { "$($Duracion[$f])s" } else { '-' }
    $md.Add("| $f | $($Resultado[$f]) | $d | ``salida/reportes/logs/$f.log`` |")
}
$md.Add('')
$md.Add('Reportes: `salida/reportes/` (gitleaks.sarif, semgrep.sarif, semgrep-muestras.sarif, muestras-normalizado.json, sonar.sarif, metodologia/candidatos-*.json).')
$md | Set-Content -Path (Join-Path $Reportes 'resumen.md') -Encoding utf8NoBOM

''
'==================== RESUMEN'
'{0,-14} {1}' -f 'FASE', 'RESULTADO'
foreach ($f in $Todas) { '{0,-14} {1}' -f $f, $Resultado[$f] }
'Detalle: salida/reportes/resumen.md'
if ($Fallas -gt 0) { Exit-ConError "$Fallas fase(s) con FALLA." }
'Todas las fases ejecutadas pasaron.'
exit 0
