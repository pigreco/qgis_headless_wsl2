#Requires -Version 5.1
<#
.SYNOPSIS
    Install QGIS headless on Windows via micromamba (conda-forge).
    Idempotent: skips any step that is already done.
.EXAMPLE
    .\setup.ps1                       # install micromamba + 'qgis' environment
                                      # (QGIS version pinned in environment.yml)
    .\setup.ps1 -AddToPath            # same, and add micromamba to the user PATH
    .\setup.ps1 -QgisVersion "3.40.*" # ignore environment.yml, install this version
#>
[CmdletBinding()]
param(
    [switch]$AddToPath,
    [string]$QgisVersion = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ENV_NAME  = "qgis"
$MAMBA_DIR = "$env:LOCALAPPDATA\micromamba"
$MAMBA_EXE = "$MAMBA_DIR\micromamba.exe"
if (-not $env:MAMBA_ROOT_PREFIX) {
    $env:MAMBA_ROOT_PREFIX = "$env:USERPROFILE\micromamba"
}

function Say { param([string]$msg) Write-Host "`n==> $msg" -ForegroundColor Blue }

# 1. micromamba ----------------------------------------------------------------
$mambaCmd = Get-Command micromamba -ErrorAction SilentlyContinue
if ($mambaCmd) {
    $MAMBA = $mambaCmd.Source
    Say "micromamba already present: $MAMBA"
} elseif (Test-Path $MAMBA_EXE) {
    $MAMBA = $MAMBA_EXE
    Say "micromamba already present: $MAMBA"
} else {
    Say "Installing micromamba in $MAMBA_DIR ..."
    New-Item -ItemType Directory -Force $MAMBA_DIR | Out-Null
    $tmpArchive = "$env:TEMP\micromamba.tar.bz2"
    $tmpExtract = "$env:TEMP\micromamba_extract"
    Invoke-WebRequest -Uri "https://micro.mamba.pm/api/micromamba/win-64/latest" `
        -OutFile $tmpArchive -UseBasicParsing
    New-Item -ItemType Directory -Force $tmpExtract | Out-Null
    tar -xjf $tmpArchive -C $tmpExtract "Library/bin/micromamba.exe"
    Copy-Item "$tmpExtract\Library\bin\micromamba.exe" $MAMBA_EXE
    Remove-Item $tmpArchive -Force
    Remove-Item $tmpExtract -Recurse -Force
    $MAMBA = $MAMBA_EXE
}
& $MAMBA --version

# 2. PATH (optional) ----------------------------------------------------------
if ($AddToPath) {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$MAMBA_DIR*") {
        Say "Adding $MAMBA_DIR to user PATH ..."
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$MAMBA_DIR", "User")
        $env:PATH += ";$MAMBA_DIR"
        Write-Host "   Reopen the terminal to use 'micromamba' directly."
    }
}

# 3. qgis environment ---------------------------------------------------------
if (Test-Path "$env:MAMBA_ROOT_PREFIX\envs\$ENV_NAME") {
    Say "Environment '$ENV_NAME' already exists: nothing to install."
} else {
    Say "Creating '$ENV_NAME' from conda-forge (~3-5 GB, a few minutes) ..."
    $envFile = Join-Path $PSScriptRoot "environment.yml"
    if ($QgisVersion) {
        & $MAMBA create -n $ENV_NAME -c conda-forge "qgis=$QgisVersion" -y
    } elseif (Test-Path $envFile) {
        Say "Using environment.yml (pinned QGIS version) ..."
        & $MAMBA create -f $envFile -y
    } else {
        & $MAMBA create -n $ENV_NAME -c conda-forge qgis -y
    }
    Say "Cleaning package cache ..."
    & $MAMBA clean -a -y
}

# 4. verify -------------------------------------------------------------------
Say "Verifying:"
$env:QT_QPA_PLATFORM = "offscreen"
$ErrorActionPreference = "Continue"
& $MAMBA run -n $ENV_NAME python -u (Join-Path $PSScriptRoot "examples\hello_qgis.py")
# 0xC0000005 = known Qt exitQgis() crash on conda-forge Windows, not a real error
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1073741819) { exit $LASTEXITCODE }
$ErrorActionPreference = "Stop"

Say "Done. Usage examples:"
Write-Host @"

  `$env:QT_QPA_PLATFORM = 'offscreen'
  & '$MAMBA' run -n $ENV_NAME qgis_process --version
  & '$MAMBA' run -n $ENV_NAME qgis_process list
  & '$MAMBA' run -n $ENV_NAME python -u examples\hello_qgis.py
"@
exit 0
