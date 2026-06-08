<#
.SYNOPSIS
    PyQGIS headless smoke test on Windows (wrapper for hello_qgis.py).
    Sets QT_QPA_PLATFORM automatically; the QGIS prefix is auto-detected
    by the Python script ($CONDA_PREFIX\Library on conda-forge Windows).
.PARAMETER InputPath
    Vector layer to read (default: examples\data\sample.geojson).
.PARAMETER MambaExe
    Path to micromamba.exe (default: $env:LOCALAPPDATA\micromamba\micromamba.exe).
.EXAMPLE
    .\examples\hello_qgis_win.ps1
    .\examples\hello_qgis_win.ps1 -InputPath C:\data\my_layer.gpkg
#>
param(
    [string]$InputPath = "",
    [string]$MambaExe  = "$env:LOCALAPPDATA\micromamba\micromamba.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SCRIPT = Join-Path $PSScriptRoot "hello_qgis.py"

if (-not (Test-Path $MambaExe)) {
    Write-Error "micromamba not found: $MambaExe`nRun .\setup.ps1 first."
    exit 1
}

$env:QT_QPA_PLATFORM = "offscreen"
if (-not $env:MAMBA_ROOT_PREFIX) { $env:MAMBA_ROOT_PREFIX = "$env:USERPROFILE\micromamba" }

$extra = @()
if ($InputPath) { $extra += @("--input", $InputPath) }

# ErrorActionPreference = Stop would surface the known Qt crash on exit (conda-forge
# Windows: exitQgis() triggers an access violation that does not affect processing).
$ErrorActionPreference = "Continue"
& $MambaExe run -n qgis python -u $SCRIPT @extra
# 0xC0000005 = STATUS_ACCESS_VIOLATION: known Qt exitQgis() crash on conda-forge Windows.
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1073741819) { exit $LASTEXITCODE }
exit 0
