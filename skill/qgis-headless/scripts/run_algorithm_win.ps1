<#
.SYNOPSIS
    Runner headless per un singolo QgsProcessingAlgorithm su Windows.
    Wrapper di run_algorithm.py: imposta QT_QPA_PLATFORM; il prefix QGIS viene
    auto-rilevato dallo script Python ($CONDA_PREFIX\Library su conda-forge Windows).
.PARAMETER Alg
    Percorso assoluto al file .py dell'algoritmo (obbligatorio).
.PARAMETER Params
    JSON dei parametri, es. '{"INPUT":"C:\\in.gpkg","OUTPUT":"memory:"}' (default: {}).
    Usa @C:\file.json per caricare da file.
.PARAMETER ClassName
    Nome della classe da usare se il modulo ne definisce piu' di una.
.PARAMETER Set
    Override di attributi del modulo prima dell'esecuzione, es. PAUSE_SECONDS=0.
    Ripeti il flag per override multipli.
.PARAMETER MambaExe
    Percorso di micromamba.exe (default: $env:LOCALAPPDATA\micromamba\micromamba.exe).
.EXAMPLE
    .\run_algorithm_win.ps1 -Alg C:\algo\buffer.py -Params '{"INPUT":"C:\\in.gpkg","DISTANCE":50,"OUTPUT":"C:\\out.gpkg"}'
    .\run_algorithm_win.ps1 -Alg C:\algo\download.py -Set PAUSE_SECONDS=0
#>
param(
    [Parameter(Mandatory)][string]$Alg,
    [string]  $Params    = "{}",
    [string]  $ClassName = "",
    [string[]]$Set       = @(),
    [string]  $MambaExe  = "$env:LOCALAPPDATA\micromamba\micromamba.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RUNNER = Join-Path $PSScriptRoot "run_algorithm.py"

if (-not (Test-Path $MambaExe)) {
    Write-Error "micromamba non trovato: $MambaExe`nEsegui prima .\setup.ps1"
    exit 1
}
if (-not (Test-Path $Alg)) {
    Write-Error "File algoritmo non trovato: $Alg"
    exit 1
}

$env:QT_QPA_PLATFORM = "offscreen"
if (-not $env:MAMBA_ROOT_PREFIX) { $env:MAMBA_ROOT_PREFIX = "$env:USERPROFILE\micromamba" }

$args_list = @("python", "-u", $RUNNER, "--alg", $Alg, "--params", $Params)
if ($ClassName) { $args_list += @("--class", $ClassName) }
foreach ($s in $Set) { $args_list += @("--set", $s) }

$ErrorActionPreference = "Continue"
& $MambaExe run -n qgis @args_list
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1073741819) { exit $LASTEXITCODE }
exit 0
