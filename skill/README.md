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
├── SKILL.md                  # istruzioni + frasi-trigger (frontmatter)
└── scripts/
    └── run_algorithm.py      # runner generico per un file QgsProcessingAlgorithm
```

## Installazione

Le skill personali stanno in `~/.claude/skills/`. Copia la cartella:

```bash
mkdir -p ~/.claude/skills
cp -r skill/qgis-headless ~/.claude/skills/
```

In alternativa, per condividerla con un team su un progetto specifico, mettila in
`<repo>/.claude/skills/qgis-headless` (così è versionata col progetto).

Riavvia/riapri Claude Code: la skill comparirà tra quelle disponibili.

## Prerequisito

L'ambiente QGIS deve esistere (`micromamba env list` deve mostrare `qgis`).
Se manca, esegui prima `bash setup.sh` dalla radice di questo repo.

## Uso del runner

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python ~/.claude/skills/qgis-headless/scripts/run_algorithm.py \
  --alg /percorso/algoritmo.py \
  --params '{"INPUT": "/percorso/input.shp", "OUTPUT": "memory:"}'
```

Dettagli completi (parametri, `--class`, `--set`) in `qgis-headless/SKILL.md`.
