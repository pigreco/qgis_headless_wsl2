#Requires -Version 5.1
<#
.SYNOPSIS
    Install (or update) the 'qgis-headless' skill for Claude Code.
    Installing and updating are the same gesture: re-run after every git pull.
    Local extra files in the installed skill (not present in the repo) are
    preserved.
.EXAMPLE
    .\install_skill.ps1             # copy into $env:USERPROFILE\.claude\skills
    .\install_skill.ps1 -Project    # copy into <repo>\.claude\skills (team, versioned)
#>
[CmdletBinding()]
param(
    [switch]$Project
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SRC = Join-Path $PSScriptRoot "skill\qgis-headless"
if (-not (Test-Path $SRC)) {
    Write-Error "Skill not found in the repo: $SRC"
    exit 1
}

$DEST_ROOT = if ($Project) { Join-Path $PSScriptRoot ".claude\skills" }
             else          { Join-Path $env:USERPROFILE ".claude\skills" }
$DEST = Join-Path $DEST_ROOT "qgis-headless"

New-Item -ItemType Directory -Force $DEST_ROOT | Out-Null

$action = if (Test-Path $DEST) { "Updated" } else { "Installed" }
New-Item -ItemType Directory -Force $DEST | Out-Null
# overwrite repo files, leave local extras untouched
Copy-Item -Recurse -Force (Join-Path $SRC "*") $DEST
Write-Host "${action}: $DEST"

$extra = Get-ChildItem -Recurse -File $DEST | Where-Object {
    $rel = $_.FullName.Substring($DEST.Length + 1)
    -not (Test-Path (Join-Path $SRC $rel))
}
if ($extra) {
    Write-Host "Local files preserved (not present in the repo):"
    $extra | ForEach-Object { Write-Host "  $($_.FullName.Substring($DEST.Length + 1))" }
}

Write-Host "Restart Claude Code to (re)load the skill."
