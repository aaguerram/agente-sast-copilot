#Requires -Version 7.0
<#
.SYNOPSIS
    Punto de entrada único para la terminal en PowerShell 7 (Windows, Linux, macOS).
    Equivalente de scripts/agente.sh, con los mismos subcomandos.

.DESCRIPTION
    Envuelve los scripts del repo; todo corre en contenedores (docker compose).

    Subcomandos:
      ayuda                 Muestra esta ayuda.
      validar [opciones]    ./scripts/validar-local.ps1 (-Solo a,b | -Saltar x | -Listar;
                            también acepta --solo/--saltar/--listar).
      rapido                Validación sin SonarQube (la fase más lenta).
      demo [ruta] [--sin-dotnet]
                            Candidatos deterministas de la metodología (pasos 1-3), SARIF de
                            Semgrep y de los analizadores de seguridad .NET sobre la ruta
                            (def. agente-sast-g7/samples/app-vulnerable), y comparación con la
                            referencia esperado/.
      objetivo <ruta> [--sin-dotnet]
                            Lo mismo que demo sobre un proyecto real (p. ej. objetivos/<p>).
          --sin-dotnet      (o -SinDotnet) No ejecuta los analizadores .NET: es el único paso
                            que COMPILA el proyecto (necesita sus paquetes NuGet). Sin él basta
                            el código fuente. Con $env:SIN_INTERNET = "1" se omite solo.
      dotnet [ruta]         Analizadores de seguridad .NET (CA2100, CA3001-CA3012, CA5350…):
                            compila cada .csproj y normaliza el SARIF con CWE/OWASP de la KB.
      comparar              Compara salida/reportes/metodologia/ con la referencia.
      ado-login             az login --use-device-code (Azure CLI en contenedor).
      replicar <org> <proy> [--real]
                            Replica el repo en Azure DevOps. Sin --real solo simula (--dry-run).
      pipeline <subcomando> scripts/ado-pipeline.sh: ejecutar --si | seguir <id>|--pr <n> |
                            descargar <id> | estado-pr <n>. Org y proyecto: --org/--project o
                            $env:ADO_ORG_URL y $env:ADO_PROJECT.

    Después, en VS Code (Copilot Chat): /demo, /metodologia, /metodologia-paso, /sast, /ayuda.

.EXAMPLE
    ./scripts/agente.ps1 demo
.EXAMPLE
    ./scripts/agente.ps1 rapido
.EXAMPLE
    ./scripts/agente.ps1 objetivo objetivos/mi-proyecto
.EXAMPLE
    ./scripts/agente.ps1 objetivo objetivos/mi-proyecto --sin-dotnet
.EXAMPLE
    ./scripts/agente.ps1 replicar https://dev.azure.com/ORG PROYECTO
.EXAMPLE
    ./scripts/agente.ps1 pipeline seguir --pr 12 --org https://dev.azure.com/ORG --project PROYECTO
#>
# Sin bloque param: el subcomando y sus opciones (incluidas las de estilo --org) llegan en $args.

. "$PSScriptRoot/_comun.ps1"

$muestra = 'agente-sast-g7/samples/app-vulnerable'
$raiz = Get-RaizRepo
Set-Location $raiz

function Show-Ayuda {
    Write-Host @'
Uso: ./scripts/agente.ps1 <subcomando> [opciones]      (bash: ./scripts/agente.sh)

  ayuda                    Esta ayuda.
  demo [ruta] [--sin-dotnet]
                           Metodología (pasos 1-3) + Semgrep + analizadores .NET sobre la app
                           vulnerable y comparación con esperado/.
  rapido                   Todas las fases locales menos SonarQube.
  validar [opciones]       Todas las fases (-Solo a,b | -Saltar x | -Listar).
  objetivo <ruta> [--sin-dotnet]
                           Como demo, sobre un proyecto real: objetivos/<proyecto>.
      --sin-dotnet         No compila: omite los analizadores .NET (basta el código fuente).
                           Con $env:SIN_INTERNET = "1" se omite solo.
  dotnet [ruta]            Solo los analizadores de seguridad .NET + normalización.
  comparar                 Resultados actuales vs. respuesta de referencia.
  ado-login                az login --use-device-code (Azure CLI en contenedor).
  replicar <org> <proy> [--real]
                           Replica en Azure DevOps. Sin --real solo simula (--dry-run).
  pipeline <subcomando>    seguir --pr <n> | seguir <id> | descargar <id> | estado-pr <n> |
                           ejecutar --si   (con --org URL --project NOM o $env:ADO_ORG_URL
                           y $env:ADO_PROJECT).

Ejemplos:
  ./scripts/agente.ps1 demo
  ./scripts/agente.ps1 objetivo objetivos/mi-proyecto
  ./scripts/agente.ps1 objetivo objetivos/mi-proyecto --sin-dotnet
  ./scripts/agente.ps1 replicar https://dev.azure.com/ORG PROYECTO
  ./scripts/agente.ps1 pipeline seguir --pr 12 --org https://dev.azure.com/ORG --project PROYECTO

En VS Code (Copilot Chat): /demo, /metodologia, /metodologia-paso, /sast, /ayuda.
'@
}

function Invoke-Py {
    # Python del contenedor "py" (no se instala nada).
    $tty = @(Get-ArgumentoTty)
    & docker compose --profile agentes run --rm @tty py @args
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Resolve-RutaRelativa {
    param([string]$Ruta)
    $r = ("$Ruta" -replace '\\', '/').TrimEnd('/')
    if ($r.StartsWith('./')) { $r = $r.Substring(2) }
    if (-not $r -or [System.IO.Path]::IsPathRooted($r) -or $r -match '^[A-Za-z]:' -or $r.Contains('..')) {
        Exit-ConError 'ERROR: indica una ruta relativa dentro del repo (p. ej. objetivos/mi-proyecto).'
    }
    if (-not (Test-Path -LiteralPath $r -PathType Container)) {
        Exit-ConError "ERROR: no existe la carpeta '$r'."
    }
    $r
}

# Analizadores .NET + normalización. Es el único paso que COMPILA el objetivo.
# Devuelve $true si terminó bien; no corta el script (el paso es opcional en demo/objetivo).
function Invoke-PasosDotnet {
    param([Parameter(Mandatory)][string]$Ruta)
    New-Item -ItemType Directory -Force -Path 'salida/reportes' | Out-Null
    # Se borra el resultado anterior: si el paso falla no queda el de otro proyecto.
    Remove-Item -Force -ErrorAction SilentlyContinue 'salida/reportes/dotnet-normalizado.json'
    $env:OBJETIVO = $Ruta
    try { & docker compose --profile seguridad run --rm -T dotnet-objetivo | Out-Host }
    finally { Remove-Item Env:OBJETIVO -ErrorAction SilentlyContinue }
    if ($LASTEXITCODE -ne 0) { return $false }
    $sarifs = @(Get-ChildItem -Path 'salida/reportes/dotnet-objetivo' -Filter '*.sarif' -ErrorAction SilentlyContinue |
        ForEach-Object { "salida/reportes/dotnet-objetivo/$($_.Name)" })
    if ($sarifs.Count -eq 0) { return $false }
    $tty = @(Get-ArgumentoTty)
    & docker compose --profile agentes run --rm @tty py agente-sast-g7/scripts/normalizar_sarif.py @sarifs `
        --base /tmp/src --prefijo $Ruta -o salida/reportes/dotnet-normalizado.json | Out-Host
    return ($LASTEXITCODE -eq 0)
}

# Separa la ruta de la opción --sin-dotnet (también -SinDotnet) en los argumentos de demo/objetivo.
function Get-OpcionesAnalisis {
    param([string[]]$Argumentos)
    $ruta = ''; $sinDotnet = $false
    foreach ($a in $Argumentos) {
        if ($a -in '--sin-dotnet', '-SinDotnet', '-sin-dotnet') { $sinDotnet = $true }
        elseif ($a.StartsWith('-')) { Exit-ConError "Opción desconocida: $a (usa --sin-dotnet)." }
        elseif ($ruta) { Exit-ConError 'ERROR: indica una sola ruta.' }
        else { $ruta = $a }
    }
    @{ Ruta = $ruta; SinDotnet = $sinDotnet }
}

function Invoke-Analisis {
    param([string]$Ruta, [switch]$SinDotnet)
    $r = Resolve-RutaRelativa $Ruta
    Test-Prerequisito
    Initialize-EntornoHost
    New-Item -ItemType Directory -Force -Path 'salida/reportes/metodologia' | Out-Null
    Write-Host ">> 1/4 Candidatos de la metodología (pasos 1-3) sobre $r"
    Invoke-Py agente-sast-g7/scripts/metodologia.py todo $r --dir salida/reportes/metodologia
    Write-Host ">> 2/4 Semgrep sobre $r"
    $env:OBJETIVO = $r
    try {
        & docker compose --profile seguridad run --rm -T semgrep-objetivo
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    finally { Remove-Item Env:OBJETIVO -ErrorAction SilentlyContinue }

    # Paso opcional: no detiene el análisis si se omite o si el proyecto no compila.
    $motivo = ''
    if ($SinDotnet) { $motivo = '--sin-dotnet' }
    elseif ($env:SIN_INTERNET -eq '1') { $motivo = 'SIN_INTERNET=1: compilar necesita los paquetes NuGet del proyecto' }
    elseif (-not (Get-ChildItem -Path $r -Recurse -Filter '*.csproj' -ErrorAction SilentlyContinue |
                Where-Object { $_.FullName -notmatch '[\\/](bin|obj)[\\/]' } | Select-Object -First 1)) {
        $motivo = "no hay ningún .csproj en $r"
    }
    $dotnetOk = $false
    if ($motivo) {
        Remove-Item -Force -ErrorAction SilentlyContinue 'salida/reportes/dotnet-normalizado.json'
        Write-Host ">> 3/4 Analizadores de seguridad .NET: omitido ($motivo)"
    }
    else {
        Write-Host ">> 3/4 Analizadores de seguridad .NET sobre $r (compila el proyecto; --sin-dotnet lo omite)"
        $dotnetOk = Invoke-PasosDotnet $r
        if (-not $dotnetOk) {
            [Console]::Error.WriteLine('AVISO: los analizadores .NET no terminaron (¿el proyecto compila?, ¿faltan paquetes NuGet?). El análisis sigue sin esa fuente.')
        }
    }

    Write-Host '>> 4/4 Comparación con la referencia'
    Invoke-Py agente-sast-g7/scripts/comparar_esperado.py
    $extra = if ($dotnetOk) { ', dotnet-normalizado.json' } else { '' }
    Write-Host @"

Listo. Reportes en salida/reportes/ (semgrep-objetivo.sarif, objetivo-normalizado.json$extra) y
salida/reportes/metodologia/ (candidatos-*.json).
Siguiente paso, en VS Code con Copilot Chat:
  /metodologia $r        (los 8 pasos con razonamiento + informe)
  /sast salida/reportes/semgrep-objetivo.sarif
"@
    if ($dotnetOk) { Write-Host '  /sast salida/reportes/dotnet-normalizado.json' }
}

function Invoke-AnalisisDotnet {
    param([string]$Ruta)
    $r = Resolve-RutaRelativa $Ruta
    Test-Prerequisito
    Initialize-EntornoHost
    Write-Host ">> Analizadores de seguridad .NET sobre $r (dotnet build en contenedor) + normalización"
    if (-not (Invoke-PasosDotnet $r)) { Exit-ConError 'ERROR: los analizadores .NET no terminaron (¿el proyecto compila?).' }
    Write-Host 'Siguiente paso, en Copilot Chat: /sast salida/reportes/dotnet-normalizado.json'
}


$argumentos = @($args | ForEach-Object { "$_" })
$cmd = if ($argumentos.Count -gt 0) { $argumentos[0] } else { 'ayuda' }
$resto = @($argumentos | Select-Object -Skip 1)

switch ($cmd) {
    { $_ -in 'ayuda', 'help', '-h', '--help', '-Help', '/?' } { Show-Ayuda; exit 0 }
    'validar' {
        # Opciones -Solo/-Saltar/-Listar o su forma bash (--solo/--saltar/--listar).
        $opciones = @{}
        for ($i = 0; $i -lt $resto.Count; $i++) {
            switch -Regex ($resto[$i]) {
                '^--?solo$' { $opciones.Solo = @($resto[++$i] -split ','); continue }
                '^--?saltar$' { $opciones.Saltar = @($resto[++$i] -split ','); continue }
                '^--?listar$' { $opciones.Listar = $true; continue }
                default { Exit-ConError "Opción desconocida para validar: $($resto[$i]) (usa -Solo, -Saltar o -Listar)." }
            }
        }
        & (Join-Path $PSScriptRoot 'validar-local.ps1') @opciones
        exit $LASTEXITCODE
    }
    'rapido' {
        & (Join-Path $PSScriptRoot 'validar-local.ps1') -Saltar sonarqube
        exit $LASTEXITCODE
    }
    'demo' {
        $op = Get-OpcionesAnalisis $resto
        Invoke-Analisis -Ruta $(if ($op.Ruta) { $op.Ruta } else { $muestra }) -SinDotnet:$op.SinDotnet
        exit 0
    }
    'objetivo' {
        $op = Get-OpcionesAnalisis $resto
        if (-not $op.Ruta) { Exit-ConError 'Uso: ./scripts/agente.ps1 objetivo objetivos/<proyecto> [--sin-dotnet]' }
        Invoke-Analisis -Ruta $op.Ruta -SinDotnet:$op.SinDotnet
        exit 0
    }
    'dotnet' { Invoke-AnalisisDotnet ($(if ($resto.Count -ge 1) { $resto[0] } else { $muestra })); exit 0 }
    'comparar' {
        Test-Prerequisito
        Initialize-EntornoHost
        Invoke-Py agente-sast-g7/scripts/comparar_esperado.py @resto
        exit 0
    }
    'ado-login' {
        & (Join-Path $PSScriptRoot 'ado.ps1') az login --use-device-code
        exit $LASTEXITCODE
    }
    'replicar' {
        if ($resto.Count -lt 2) { Exit-ConError 'Uso: ./scripts/agente.ps1 replicar https://dev.azure.com/ORG PROYECTO [--real]' }
        $extra = @($resto | Select-Object -Skip 2)
        $modo = @('--dry-run')
        if ($extra.Count -gt 0 -and $extra[0] -in '--real', '-Real') {
            $modo = @()
            $extra = @($extra | Select-Object -Skip 1)
        }
        & (Join-Path $PSScriptRoot 'ado.ps1') bash scripts/ado-bootstrap.sh --org $resto[0] --project $resto[1] @modo @extra
        exit $LASTEXITCODE
    }
    'pipeline' {
        if ($resto.Count -lt 1) { Exit-ConError 'Uso: ./scripts/agente.ps1 pipeline seguir --pr <n> | descargar <id> | estado-pr <n> | ejecutar --si' }
        & (Join-Path $PSScriptRoot 'ado.ps1') bash scripts/ado-pipeline.sh @resto
        exit $LASTEXITCODE
    }
    default {
        [Console]::Error.WriteLine("Subcomando desconocido: $cmd")
        Show-Ayuda
        exit 1
    }
}
