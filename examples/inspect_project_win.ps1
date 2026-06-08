<#
.SYNOPSIS
    Ispeziona un progetto QGIS (.qgs / .qgz) headless su Windows.
    Stampa titolo, CRS, lista layer con tipo, geometria, campi, feature count.
    Wrapper di inspect_project.py: imposta QT_QPA_PLATFORM; il prefix QGIS viene
    auto-rilevato dallo script Python ($CONDA_PREFIX\Library su conda-forge Windows).
.PARAMETER Project
    Percorso al file .qgs o .qgz (obbligatorio).
.PARAMETER MambaExe
    Percorso a micromamba.exe (default: $env:LOCALAPPDATA\micromamba\micromamba.exe).
.EXAMPLE
    .\examples\inspect_project_win.ps1 -Project C:\lavoro\progetto.qgs
#>
param(
    [Parameter(Mandatory)][string]$Project,
    [string]$MambaExe = "$env:LOCALAPPDATA\micromamba\micromamba.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SCRIPT = Join-Path $PSScriptRoot "inspect_project.py"

if (-not (Test-Path $MambaExe)) {
    Write-Error "micromamba non trovato: $MambaExe`nEsegui prima .\setup.ps1"
    exit 1
}
if (-not (Test-Path $Project)) {
    Write-Error "File progetto non trovato: $Project"
    exit 1
}

$env:QT_QPA_PLATFORM = "offscreen"
if (-not $env:MAMBA_ROOT_PREFIX) { $env:MAMBA_ROOT_PREFIX = "$env:USERPROFILE\micromamba" }

$ErrorActionPreference = "Continue"
& $MambaExe run -n qgis python -u $SCRIPT --project $Project
# 0xC0000005 = crash noto di exitQgis() su conda-forge Windows, non e' un errore reale
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1073741819) { exit $LASTEXITCODE }
exit 0
