# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate in questo file.

---

## [1.1.0] — 2026-08-07

Campagna di migliorie significative: CI multi-piattaforma, ambiente riproducibile,
supporto ARM, potenziamento del runner, rendering headless, installer della skill,
documentazione completa.

### Aggiunte

- **CI multi-piattaforma** — GitHub Actions su Ubuntu x86_64, Ubuntu ARM
  (`ubuntu-24.04-arm`), e Windows, con cache dell'ambiente e validazione
  smoke test a ogni push/PR. Template copiabile per algoritmi QGIS in CI.
  ([PR #7](https://github.com/pigreco/qgis_headless_wsl2/pull/7))

- **Ambiente riproducibile** — `environment.yml` con QGIS pinnato a 3.44.11,
  usato da setup e CI, garantisce lo stesso ambiente per tutti gli utenti.
  ([PR #8](https://github.com/pigreco/qgis_headless_wsl2/pull/8))

- **Supporto ARM** — `setup.sh` rileva l'architettura (x86_64 / aarch64) e
  scarica il binario micromamba corretto; job CI dedicato valida il supporto
  su Linux ARM (WSL2 su Windows on ARM, Raspberry Pi, ecc).
  ([PR #9](https://github.com/pigreco/qgis_headless_wsl2/pull/9))

- **Potenziamento del runner** (`run_algorithm.py`):
  - Raster nei `--params`: file `.tif .vrt .asc` ecc. vengono caricati come
    `QgsRasterLayer`, non come vettoriale.
  - Parametri validati con `checkParameterValues()` prima dell'esecuzione:
    errori di parametri falliscono subito con messaggio chiaro.
  - Flag `--project` per caricare un `.qgs/.qgz` nel processing context,
    consentendo agli algoritmi di usare i layer del progetto.
  ([PR #10](https://github.com/pigreco/qgis_headless_wsl2/pull/10))

- **Rendering headless** — nuovo `examples/render_map.py`: renderizza mappe
  in PNG senza aprire QGIS via `QgsMapRendererParallelJob`. Layer singoli
  (con stile QML opzionale) oppure interi progetti; utile per report automatici,
  anteprime, mappe in pipeline/CI. Testato con il DTM Etna: 1200×1259 px in 1,6 s.
  ([PR #11](https://github.com/pigreco/qgis_headless_wsl2/pull/11))

- **Output JSON per inspect** — `inspect_project.py --json` emette JSON pulito
  e machine-readable (pipe-abile in `jq`), con struttura completa di metadati
  di progetto e layer; output umano invariato.
  ([PR #12](https://github.com/pigreco/qgis_headless_wsl2/pull/12))

- **Batch CSV per Verto Online** — `verto_online.py --csv punti.csv --output
  convertiti.csv` converte coordinate in batch (con chunking automatico a
  32.000 punti, il limite del servizio IGM). Riconoscimento automatico di
  header (`e,n` / `est,nord` / `x,y`) e delimitatore.
  ([PR #13](https://github.com/pigreco/qgis_headless_wsl2/pull/13))

- **Installer della skill** — `install_skill.sh` (WSL2/Linux) e `install_skill.ps1`
  (Windows): installazione e aggiornamento della skill Claude Code con un comando.
  Opzioni: `--project` per team (versionata nel repo), `--symlink` per link vivo al
  checkout. Preserva file locali extra (es. `SETUP.md` personalizzato).
  ([PR #14](https://github.com/pigreco/qgis_headless_wsl2/pull/14))

- **File di dati di esempio** — `examples/data/sample_points_3003.csv` per
  il batch Verto Online; `.gitignore` per escludere raster locali di prova
  (*.tif) e cache Python.

### Modifiche

- **README completo** — introduzione riscritta per descrivere il ciclo headless
  completo (processing → ispezione → rendering); indice cliccabile; quick start
  aggiornate con note su versione pinnata e opzioni; contenuto del repo riorganizzato
  per aree (setup, esempi, skill, CI); sezione Uso espansa con renderer e ispezione
  JSON; prerequisiti distinti per WSL2 e Windows nativo.
  ([PR #15](https://github.com/pigreco/qgis_headless_wsl2/pull/15))

- **Skill di Claude Code** — aggiornata con i nuovi flag di `run_algorithm.py`;
  `skill/README.md` sostituisce copy-paste manuale con installer one-command.

- **Documentazione PyQGIS** — scheletro aggiornato nel README con il pattern
  anti-segfault: lavoro in funzione separata, `gc.collect()` prima di
  `exitQgis()`. Viene descritto anche il bug stesso nella tabella
  "Risoluzione problemi".

### Correzioni

- **Segfault all'uscita** — `hello_qgis.py` e `inspect_project.py` rifattorizzati
  con lo stesso pattern di `run_algorithm.py` (funzione separata + `gc.collect()`
  prima di `exitQgis()`). QGIS ≥3.44.10 su conda-forge: layer GDAL/OGR ancora
  referenziati quando il provider registry viene smantellato segfault l'interprete
  in uscita. CI (QGIS 3.44.11) ha scovato il bug.
  ([PR #7](https://github.com/pigreco/qgis_headless_wsl2/pull/7))

- **Typo nel README** — frase mista italiano/inglese ("~hundreds of MB" → "di
  alcune centinaia di MB"); sezioni duplicate in examples/README (due "3.").
  ([PR #6](https://github.com/pigreco/qgis_headless_wsl2/pull/6))

### Note

- Il **flag `--version` per `setup.sh`** e `-QgisVersion` per `setup.ps1` permette
  di installare una versione QGIS diversa da quella pinnata in `environment.yml`.
- La **CI esclude gli esempi Verto Online** (servizio IGM reale: no dipendenza
  esterna né traffico inutile).
- **Windows conda-forge**: il crash noto di `exitQgis()` (0xC0000005) rimappa
  l'exit code; gli step CI tolerano il crash controllando un marker di successo
  nell'output del processo, non il codice di uscita.

---

## [1.0.0] — 2024-06 (originale)

Progetto iniziale di @pigreco: guida passo-passo per installare QGIS headless
via micromamba su WSL2/Linux. Supporto Windows aggiunto da @aborruso (PR #2).

### Contenuto base

- `setup.sh` — installazione one-shot idempotente per WSL2/Linux.
- `setup.ps1` — installazione one-shot idempotente per Windows nativo (PR #2).
- `examples/hello_qgis.py` / `hello_qgis_win.ps1` — smoke test PyQGIS.
- `examples/inspect_project.py` — ispezionare un progetto `.qgs/.qgz`.
- `examples/verto_online.py` / `verto_processing_algorithm.py` — conversione
  coordinate con API IGM Verto Online.
- `skill/qgis-headless/` — skill per Claude Code, runner generico per
  `QgsProcessingAlgorithm` singolo file.
- README in italiano con guida manuale (Passi 1–5).

---

## Note sulla versione

- **1.1.0 è una major update** — aggiunge feature significative (rendering,
  JSON, CSV batch, installer) e correzioni di bug reale (segfault). Retrocompatibile
  per il codice PyQGIS/Processing.
- Tutte le PR della campagna 1.1.0 sono testate su CI multi-piattaforma;
  il badge nel README lo dimostra.
