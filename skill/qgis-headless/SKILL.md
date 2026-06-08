---
name: qgis-headless
description: Run or test QGIS Processing algorithms and PyQGIS code headless (no GUI) on WSL/Linux or Windows via a conda-forge QGIS environment (micromamba). Use when asked to run/test a QGIS Processing algorithm or script, run qgis_process, execute PyQGIS without opening the desktop, or validate a single-file QgsProcessingAlgorithm. Prefer this over the QGIS MCP server when the desktop need not be involved.
---

# QGIS Headless Runner

Run QGIS Processing algorithms and arbitrary PyQGIS **without the desktop GUI**,
using a conda-forge QGIS environment managed by `micromamba`. This is the fast,
autonomous path for testing — no running QGIS Desktop, no MCP "Start Server".

## When to use this vs the QGIS MCP server

- **Use this skill** to run/test an algorithm or PyQGIS code from the shell,
  for CI-style validation, or when the user's QGIS Desktop is not running.
- **Use the QGIS MCP tools** (`mcp__qgis__*`) instead when the user wants to act
  on their **live desktop project** (load layers into the open project, render
  the canvas, etc.). The two coexist.

For a full, narrated setup guide (Italian), see the repository README:
https://github.com/pigreco/qgis_headless_wsl2#readme

## WSL2/Linux vs Windows

The setup differs by platform; the Python scripts (`run_algorithm.py`,
`hello_qgis.py`, `inspect_project.py`) work on both — the QGIS prefix path is
auto-detected at runtime (`$CONDA_PREFIX\Library` on conda-forge Windows,
`$CONDA_PREFIX` on Linux).

| | WSL2 / Linux | Windows nativo |
|---|---|---|
| Setup script | `bash setup.sh` | `.\setup.ps1` |
| micromamba binary | `~/.local/bin/micromamba` | `$env:LOCALAPPDATA\micromamba\micromamba.exe` |
| Env prefix | `~/micromamba` | `$env:USERPROFILE\micromamba` |
| QGIS prefix | `$CONDA_PREFIX` | `$CONDA_PREFIX\Library` (auto) |
| Shell env var | `export QT_QPA_PLATFORM=offscreen` | `$env:QT_QPA_PLATFORM = "offscreen"` |

**Windows invocation example (use the PowerShell wrappers):**
```powershell
# smoke test
.\examples\hello_qgis_win.ps1

# inspect a QGIS project
.\examples\inspect_project_win.ps1 -Project C:\path\to\project.qgs

# custom algorithm
.\skill\qgis-headless\scripts\run_algorithm_win.ps1 `
    -Alg C:\path\to\algorithm.py `
    -Params '{"INPUT":"C:\\path\\to\\input.gpkg","OUTPUT":"memory:"}'
```
The wrappers set `QT_QPA_PLATFORM=offscreen` automatically; no manual
configuration needed.

---

## Step 0 — Verify (or create) the environment

The env is user-level (in `$HOME`), so it works from any folder/workspace.

**WSL2/Linux:**
```bash
micromamba env list 2>/dev/null | grep -q qgis && echo "qgis env present" || echo "missing"
```

**Windows (PowerShell):**
```powershell
& "$env:LOCALAPPDATA\micromamba\micromamba.exe" env list | Select-String "qgis"
```

If `micromamba` is not on PATH, the binary may be at `~/.local/bin/micromamba`
(Linux) or `$env:LOCALAPPDATA\micromamba\micromamba.exe` (Windows).

If the env is **missing**, create it (downloads ~3–5 GB, takes a few minutes):

**WSL2/Linux:**
```bash
# install micromamba if needed
mkdir -p ~/.local/bin && curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
  | tar -xj -C /tmp bin/micromamba && cp /tmp/bin/micromamba ~/.local/bin/ && chmod +x ~/.local/bin/micromamba
# create the env, then free the download cache
export MAMBA_ROOT_PREFIX="$HOME/micromamba"
~/.local/bin/micromamba create -n qgis -c conda-forge qgis -y
~/.local/bin/micromamba clean -a -y
```

**Windows (PowerShell):**
```powershell
.\setup.ps1    # installs micromamba + qgis env; idempotent
```

Always confirm before a multi-GB install if the user has not already asked for it.

## Running things

Headless Qt needs an offscreen platform. Two equivalent invocation styles:

```bash
# A) one-off, no shell config needed
MAMBA_ROOT_PREFIX=$HOME/micromamba QT_QPA_PLATFORM=offscreen \
  ~/.local/bin/micromamba run -n qgis <command>

# B) if `micromamba shell init` was run (activate works in any terminal)
micromamba activate qgis && export QT_QPA_PLATFORM=offscreen
```

### Quick info / built-in algorithms

```bash
micromamba run -n qgis qgis_process --version
micromamba run -n qgis qgis_process list            # registered algorithms
micromamba run -n qgis qgis_process run native:buffer -- INPUT=in.shp DISTANCE=10 OUTPUT=out.gpkg
```

### A single-file QgsProcessingAlgorithm (not registered as a plugin)

Use the bundled generic runner, which initializes QGIS headless, imports the
module, finds the `QgsProcessingAlgorithm` subclass, and calls
`processAlgorithm()`:

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python ~/.claude/skills/qgis-headless/scripts/run_algorithm.py \
  --alg /path/to/my_algorithm.py \
  --params '{"INPUT": "/path/to/input.shp", "OUTPUT": "memory:"}'
```

- In `--params`, any string value that is an **existing file path** is loaded as
  a vector layer; everything else is passed through (booleans, ints, `"memory:"`,
  output paths, enum indices, …).
- `--class NAME` if the module defines more than one algorithm class.
- Add `python -u` (or it is set automatically) to avoid losing buffered stdout if
  the run crashes; pipe through `tail`/`grep` to keep output readable.

## Tips & gotchas

- **Network algorithms** (e.g. WFS downloaders with sleeps): override pause
  constants for tests via the module, e.g. set `mod.PAUSE_SECONDS` low. Keep the
  real value for production runs — don't hammer public services.
- **CRS/PROJ**: the conda-forge build ships its own PROJ data; CRS transforms
  work out of the box.
- **Output**: `"memory:"` keeps results in the context; read counts with
  `context.getMapLayer(result["OUTPUT"]).featureCount()`. Use a file path
  (`.gpkg`, `.shp`) to persist.
- **stdout buffering**: when piping, prefer `python -u` so progress prints appear
  even on failure.
- This QGIS is **separate** from the user's desktop QGIS — plugins, profiles and
  settings are not shared. To reproduce desktop-specific behavior, use the MCP.
