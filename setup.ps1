#Requires -Version 5.1
<#
.SYNOPSIS
    Installa QGIS headless su Windows via micromamba (conda-forge).
    Idempotente: non reinstalla nulla se gia' presente.
.EXAMPLE
    .\setup.ps1               # installa micromamba + ambiente 'qgis'
    .\setup.ps1 -AddToPath    # come sopra, aggiunge micromamba al PATH utente
#>
[CmdletBinding()]
param(
    [switch]$AddToPath
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
    Say "micromamba gia' presente: $MAMBA"
} elseif (Test-Path $MAMBA_EXE) {
    $MAMBA = $MAMBA_EXE
    Say "micromamba gia' presente: $MAMBA"
} else {
    Say "Installo micromamba in $MAMBA_DIR ..."
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

# 2. PATH (opzionale) ---------------------------------------------------------
if ($AddToPath) {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$MAMBA_DIR*") {
        Say "Aggiungo $MAMBA_DIR al PATH utente ..."
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$MAMBA_DIR", "User")
        $env:PATH += ";$MAMBA_DIR"
        Write-Host "   Riapri il terminale per usare 'micromamba' direttamente."
    }
}

# 3. ambiente qgis -------------------------------------------------------------
if (Test-Path "$env:MAMBA_ROOT_PREFIX\envs\$ENV_NAME") {
    Say "Ambiente '$ENV_NAME' gia' esistente: nessuna installazione."
} else {
    Say "Creo '$ENV_NAME' da conda-forge (~3-5 GB, qualche minuto) ..."
    & $MAMBA create -n $ENV_NAME -c conda-forge qgis -y
    Say "Pulisco la cache dei pacchetti ..."
    & $MAMBA clean -a -y
}

# 4. verifica ------------------------------------------------------------------
Say "Verifica:"
$env:QT_QPA_PLATFORM = "offscreen"
$ErrorActionPreference = "Continue"
& $MAMBA run -n $ENV_NAME python -u (Join-Path $PSScriptRoot "examples\hello_qgis.py")
# 0xC0000005 = crash noto di Qt exitQgis() su conda-forge Windows, non e' un errore reale
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1073741819) { exit $LASTEXITCODE }
$ErrorActionPreference = "Stop"

Say "Fatto. Esempi d'uso:"
Write-Host @"

  `$env:QT_QPA_PLATFORM = 'offscreen'
  & '$MAMBA' run -n $ENV_NAME qgis_process --version
  & '$MAMBA' run -n $ENV_NAME qgis_process list
  & '$MAMBA' run -n $ENV_NAME python -u examples\hello_qgis.py
"@
exit 0
