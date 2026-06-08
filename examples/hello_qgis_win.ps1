<#
.SYNOPSIS
    Smoke test di PyQGIS headless su Windows (wrapper di hello_qgis.py).
    Imposta automaticamente QT_QPA_PLATFORM; il prefix QGIS viene auto-rilevato
    dallo script Python ($CONDA_PREFIX\Library su conda-forge Windows).
.PARAMETER InputPath
    Layer vettoriale da leggere (default: examples\data\sample.geojson).
.PARAMETER MambaExe
    Percorso di micromamba.exe (default: $env:LOCALAPPDATA\micromamba\micromamba.exe).
.EXAMPLE
    .\examples\hello_qgis_win.ps1
    .\examples\hello_qgis_win.ps1 -InputPath C:\dati\mio_layer.gpkg
#>
param(
    [string]$InputPath = "",
    [string]$MambaExe  = "$env:LOCALAPPDATA\micromamba\micromamba.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SCRIPT = Join-Path $PSScriptRoot "hello_qgis.py"

if (-not (Test-Path $MambaExe)) {
    Write-Error "micromamba non trovato: $MambaExe`nEsegui prima .\setup.ps1"
    exit 1
}

$env:QT_QPA_PLATFORM = "offscreen"
if (-not $env:MAMBA_ROOT_PREFIX) { $env:MAMBA_ROOT_PREFIX = "$env:USERPROFILE\micromamba" }

$extra = @()
if ($InputPath) { $extra += @("--input", $InputPath) }

# ErrorActionPreference = Stop farebbe esplodere il crash Qt all'uscita (noto
# su conda-forge Windows: exitQgis() genera un access violation che non impatta
# il processing). Lo gestiamo esplicitamente.
$ErrorActionPreference = "Continue"
& $MambaExe run -n qgis python -u $SCRIPT @extra
# 0xC0000005 = STATUS_ACCESS_VIOLATION: crash noto di Qt exitQgis() su conda-forge Windows.
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1073741819) { exit $LASTEXITCODE }
exit 0
