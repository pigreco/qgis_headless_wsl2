<#
.SYNOPSIS
    Inspect a QGIS project (.qgs / .qgz) headless on Windows.
    Prints title, CRS, and per-layer info: type, geometry, fields, feature count.
    Wrapper for inspect_project.py: sets QT_QPA_PLATFORM; the QGIS prefix is
    auto-detected by the Python script ($CONDA_PREFIX\Library on conda-forge Windows).
.PARAMETER Project
    Path to the .qgs or .qgz file (required).
.PARAMETER MambaExe
    Path to micromamba.exe (default: $env:LOCALAPPDATA\micromamba\micromamba.exe).
.EXAMPLE
    .\examples\inspect_project_win.ps1 -Project C:\work\project.qgs
#>
param(
    [Parameter(Mandatory)][string]$Project,
    [string]$MambaExe = "$env:LOCALAPPDATA\micromamba\micromamba.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SCRIPT = Join-Path $PSScriptRoot "inspect_project.py"

if (-not (Test-Path $MambaExe)) {
    Write-Error "micromamba not found: $MambaExe`nRun .\setup.ps1 first."
    exit 1
}
if (-not (Test-Path $Project)) {
    Write-Error "Project file not found: $Project"
    exit 1
}

$env:QT_QPA_PLATFORM = "offscreen"
if (-not $env:MAMBA_ROOT_PREFIX) { $env:MAMBA_ROOT_PREFIX = "$env:USERPROFILE\micromamba" }

$ErrorActionPreference = "Continue"
& $MambaExe run -n qgis python -u $SCRIPT --project $Project
# 0xC0000005 = known Qt exitQgis() crash on conda-forge Windows, not a real error
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1073741819) { exit $LASTEXITCODE }
exit 0
