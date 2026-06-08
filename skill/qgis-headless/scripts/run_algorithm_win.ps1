<#
.SYNOPSIS
    Headless runner for a single QgsProcessingAlgorithm on Windows.
    Wrapper for run_algorithm.py: sets QT_QPA_PLATFORM; the QGIS prefix is
    auto-detected by the Python script ($CONDA_PREFIX\Library on conda-forge Windows).
.PARAMETER Alg
    Absolute path to the algorithm .py file (required).
.PARAMETER Params
    JSON parameter dict, e.g. '{"INPUT":"C:\\in.gpkg","OUTPUT":"memory:"}' (default: {}).
    Use @C:\file.json to load from a file.
.PARAMETER ClassName
    Class name to use if the module defines more than one algorithm.
.PARAMETER Set
    Override a module attribute before running, e.g. PAUSE_SECONDS=0.
    Repeat the flag for multiple overrides.
.PARAMETER MambaExe
    Path to micromamba.exe (default: $env:LOCALAPPDATA\micromamba\micromamba.exe).
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
    Write-Error "micromamba not found: $MambaExe`nRun .\setup.ps1 first."
    exit 1
}
if (-not (Test-Path $RUNNER)) {
    Write-Error "Runner not found: $RUNNER`nCheck that the repository is intact."
    exit 1
}
if (-not (Test-Path $Alg)) {
    Write-Error "Algorithm file not found: $Alg"
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
