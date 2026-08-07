# Skill `qgis-headless` per Claude Code

Una [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills) che insegna
a **Claude Code** a eseguire/testare algoritmi QGIS Processing e codice PyQGIS in
modalità headless, usando l'ambiente `qgis` creato con questo repo.

Quando è installata, Claude la attiva da solo quando chiedi cose come *"testa
questo algoritmo QGIS headless"*, *"esegui qgis_process"*, *"valida questo
QgsProcessingAlgorithm"*, oppure esplicitamente con `/qgis-headless`.

## Contenuto

```
qgis-headless/
├── SKILL.md                      # istruzioni + frasi-trigger (frontmatter)
└── scripts/
    ├── run_algorithm.py          # runner generico per un file QgsProcessingAlgorithm
    └── run_algorithm_win.ps1     # wrapper PowerShell per Windows
```

## Installazione (e aggiornamento)

Un solo comando, lo stesso anche per aggiornare dopo un `git pull`:

**WSL2/Linux:**
```bash
bash install_skill.sh              # copia in ~/.claude/skills/
bash install_skill.sh --project    # oppure in <repo>/.claude/skills/ (team)
bash install_skill.sh --symlink    # symlink al repo: si aggiorna col pull
```

**Windows (PowerShell):**
```powershell
.\install_skill.ps1                # copia in $env:USERPROFILE\.claude\skills
.\install_skill.ps1 -Project       # oppure in <repo>\.claude\skills (team)
```

Eventuali file locali aggiunti alla skill installata (non presenti nel repo)
vengono preservati e segnalati. Riavvia/riapri Claude Code: la skill comparirà
tra quelle disponibili.

## Prerequisito

L'ambiente QGIS deve esistere (`micromamba env list` deve mostrare `qgis`).
Se manca:
- **WSL2/Linux:** esegui `bash setup.sh` dalla radice di questo repo.
- **Windows:** esegui `.\setup.ps1` dalla radice di questo repo.

## Uso del runner

**WSL2/Linux:**
```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python ~/.claude/skills/qgis-headless/scripts/run_algorithm.py \
  --alg /percorso/algoritmo.py \
  --params '{"INPUT": "/percorso/input.shp", "OUTPUT": "memory:"}'
```

**Windows (PowerShell):**
```powershell
.\skill\qgis-headless\scripts\run_algorithm_win.ps1 `
    -Alg C:\percorso\algoritmo.py `
    -Params '{"INPUT":"C:\\percorso\\input.gpkg","OUTPUT":"memory:"}'
```

Dettagli completi (parametri, `--class`, `--set`) in `qgis-headless/SKILL.md`.
