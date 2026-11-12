#Requires -Version 7.0
<#
.SYNOPSIS
    Ejecuta, sigue y descarga el pipeline de seguridad de Azure DevOps por la API REST.
    Equivalente en PowerShell 7 de scripts/ado-pipeline.sh, con las MISMAS opciones.

.DESCRIPTION
    Corre scripts/ado-pipeline.sh dentro del contenedor de Azure CLI (scripts/ado.ps1).
    Autenticación: $env:AZURE_DEVOPS_EXT_PAT si existe; si no, la sesión de
    "./scripts/ado.ps1 az login --use-device-code". El token nunca se escribe en disco.

    Subcomandos:
      ejecutar [--rama main] --si        Encola el pipeline (consume minutos: exige --si).
      seguir <buildId>                   Espera a que termine y muestra el resultado por job.
      seguir --pr <n> | --rama <rama>    Igual, sobre el último build del PR o de la rama.
      descargar <buildId> [--artefacto CodeAnalysisLogs] [--dir salida/reportes/pipeline-<id>]
      estado-pr <n>                      Estado del PR, mergeStatus y su último build.

    Opciones comunes: --org URL, --project NOM, --repo NOM, --pipeline NOM,
    --intervalo S (def. 30), --timeout S (def. 3600). O $env:ADO_ORG_URL / $env:ADO_PROJECT.
    Códigos de salida de "seguir": 0 succeeded, 1 otro resultado, 2 timeout.

.EXAMPLE
    ./scripts/ado-pipeline.ps1 --org https://dev.azure.com/ORG --project PROY seguir --pr 30
.EXAMPLE
    ./scripts/ado-pipeline.ps1 --org https://dev.azure.com/ORG --project PROY descargar 55
#>
# Sin bloque param: las opciones estilo --org pasan tal cual al script bash.

if ($args.Count -gt 0 -and $args[0] -in @('-Help', '/?')) {
    Get-Help $PSCommandPath -Detailed
    exit 0
}
& (Join-Path $PSScriptRoot 'ado.ps1') bash scripts/ado-pipeline.sh @args
exit $LASTEXITCODE
