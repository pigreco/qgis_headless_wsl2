# QGIS headless via micromamba (WSL2 + Windows)

[![CI](https://github.com/pigreco/qgis_headless_wsl2/actions/workflows/ci.yml/badge.svg)](https://github.com/pigreco/qgis_headless_wsl2/actions/workflows/ci.yml)

Guida passo-passo per installare e usare **QGIS senza interfaccia grafica** —
in WSL2 (Linux su Windows, x86_64 e ARM) o su Windows nativo (PowerShell) —
per l'intero ciclo headless: eseguire e testare algoritmi QGIS Processing,
codice PyQGIS, ispezionare progetti e **renderizzare mappe in PNG**, da
terminale o in automazione, senza mai aprire il desktop. Tutto è verificato
dalla CI su tre piattaforme (Ubuntu x86_64, Ubuntu ARM, Windows).

> "Headless" = nessuna finestra. Per Qt serve un *platform plugin* offscreen:
> `export QT_QPA_PLATFORM=offscreen` (Linux) / `$env:QT_QPA_PLATFORM = "offscreen"` (Windows).

**Indice**: [Avvio rapido WSL2](#avvio-rapido--wsl2-script-automatico) ·
[Avvio rapido Windows](#avvio-rapido--windows-nativo-senza-wsl2) ·
[Contenuto del repo](#contenuto-del-repo) ·
[Prerequisiti](#prerequisiti) ·
[Guida manuale (Passi 1–5)](#passo-1--installare-micromamba-un-singolo-binario) ·
[Uso](#uso) ·
[Manutenzione](#manutenzione) ·
[Risoluzione problemi](#risoluzione-problemi) ·
[Note](#note)

---

## Avvio rapido — WSL2 (script automatico)

Per chi vuole configurarsi l'ambiente con **un solo comando** (lo script è
idempotente: non reinstalla nulla se è già presente):

```bash
git clone https://github.com/pigreco/qgis_headless_wsl2.git
cd qgis_headless_wsl2
bash setup.sh                  # installa micromamba (se manca) + l'ambiente 'qgis'
# opzioni:
bash setup.sh --init           # attiva 'micromamba activate' in ogni terminale
bash setup.sh --version 3.40.* # una versione QGIS diversa da quella pinnata
```

La versione QGIS installata è **pinnata in `environment.yml`** (la stessa
validata dalla CI): ambiente riproducibile, uguale per tutti. Funziona su
x86_64 **e** ARM (l'architettura è rilevata automaticamente).

Al termine verifica con:

```bash
QT_QPA_PLATFORM=offscreen ~/.local/bin/micromamba run -n qgis qgis_process --version
```

Chi preferisce capire ogni passaggio può seguire la guida manuale qui sotto.

---

## Avvio rapido — Windows nativo (senza WSL2)

Per chi vuole girare tutto in **PowerShell nativo** (niente WSL2), usa `setup.ps1`:

```powershell
git clone https://github.com/pigreco/qgis_headless_wsl2.git
cd qgis_headless_wsl2
.\setup.ps1                        # installa micromamba + ambiente 'qgis'
# opzioni:
.\setup.ps1 -AddToPath             # aggiunge micromamba al PATH utente
.\setup.ps1 -QgisVersion "3.40.*"  # una versione QGIS diversa da quella pinnata
```

Al termine verifica con:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
& "$env:LOCALAPPDATA\micromamba\micromamba.exe" run -n qgis qgis_process --version
```

Smoke test, ispezione progetti e runner algoritmico con wrapper PowerShell dedicati:

```powershell
# smoke test
.\examples\hello_qgis_win.ps1

# ispeziona un progetto QGIS
.\examples\inspect_project_win.ps1 -Project C:\lavoro\progetto.qgs

# algoritmo personalizzato
.\skill\qgis-headless\scripts\run_algorithm_win.ps1 `
    -Alg C:\path\to\algorithm.py `
    -Params '{"INPUT":"C:\\in.gpkg","OUTPUT":"memory:"}'
```

> I wrapper impostano `QT_QPA_PLATFORM=offscreen` automaticamente.
> Il prefix QGIS (`$CONDA_PREFIX\Library` su conda-forge Windows) è
> **auto-rilevato** dagli script Python: nessuna configurazione manuale.
> Gli stessi script Python funzionano invariati anche in WSL2/Linux.

### Variabili d'ambiente consigliate (opzionale)

Per non dover ripetere il path di micromamba ad ogni sessione, puoi aggiungere
queste variabili al profilo utente Windows (Impostazioni di sistema → Variabili
d'ambiente, oppure da PowerShell con `[Environment]::SetEnvironmentVariable`):

| Variabile | Valore consigliato | Scopo |
|---|---|---|
| `MAMBA_ROOT_PREFIX` | `%USERPROFILE%\micromamba` | Root degli ambienti micromamba |
| `QT_QPA_PLATFORM` | `offscreen` | Evita di doverlo impostare ogni volta |

In alternativa aggiungili al tuo profilo PowerShell (`$PROFILE`):

```powershell
$env:MAMBA_ROOT_PREFIX  = "$env:USERPROFILE\micromamba"
$env:QT_QPA_PLATFORM    = "offscreen"
```

---

## Contenuto del repo

**Setup e ambiente**

- `setup.sh` / `setup.ps1` — installazione one-shot idempotente
  (WSL2/Linux e Windows nativo).
- `environment.yml` — definizione dell'ambiente con la **versione QGIS pinnata**
  (la stessa usata dalla CI): tutti ottengono un ambiente riproducibile. Gli
  script di setup lo usano automaticamente; per una versione diversa:
  `bash setup.sh --version 3.40.*` / `.\setup.ps1 -QgisVersion "3.40.*"`.

**Esempi** (dettagli in [examples/README.md](examples/README.md))

- `hello_qgis.py` / `hello_qgis_win.ps1` — smoke test: verifica l'ambiente.
- `inspect_project.py` / `inspect_project_win.ps1` — ispeziona un progetto
  `.qgs`/`.qgz`; con `--json` emette output machine-readable (pipe-abile in `jq`).
- `centroids_algorithm.py` — `QgsProcessingAlgorithm` offline minimale per
  provare il runner generico (usato anche dalla CI).
- `render_map.py` — renderizza una mappa in **PNG senza aprire QGIS**
  (layer con stile QML o interi progetti): report automatici, anteprime,
  mappe in pipeline/CI.
- `verto_online.py` / `verto_processing_algorithm.py` — conversione di
  coordinate con l'API ufficiale IGM **Verto Online**, anche batch da CSV
  (`--csv punti.csv --output convertiti.csv`, chunking automatico).

**Skill per Claude Code**

- `skill/` — la skill **`qgis-headless`**: insegna a Claude Code a
  eseguire/testare algoritmi QGIS headless con un runner generico
  (raster e vettoriali nei parametri, `--project`, validazione).
  Installazione e aggiornamento con un comando: `bash install_skill.sh`
  (anche `--project` per il team, `--symlink` per chi sviluppa) o
  `.\install_skill.ps1`. Dettagli in [skill/README.md](skill/README.md).

**CI**

- `.github/workflows/ci.yml` — GitHub Actions: crea l'ambiente QGIS da zero su
  **Ubuntu x86_64, Ubuntu ARM e Windows** e a ogni push/PR esercita smoke test,
  `qgis_process`, runner generico, ispezione progetti e rendering. È anche un
  template copiabile per chi vuole testare i propri algoritmi QGIS in CI.

Verifica veloce dopo l'installazione:

```bash
# WSL2/Linux
QT_QPA_PLATFORM=offscreen micromamba run -n qgis python examples/hello_qgis.py
```

```powershell
# Windows
.\examples\hello_qgis_win.ps1
```

---

## Prerequisiti

Per la via **WSL2** (guida manuale qui sotto):

- **WSL2** già attivo con una distro Linux (es. Ubuntu), x86_64 o ARM.
  Verifica da Windows: `wsl -l -v` (la colonna VERSION deve essere `2`).
- Connessione a Internet dentro WSL (il download è di alcune centinaia di MB).
- ~5 GB liberi nella home WSL (`df -h ~`).

Per la via **Windows nativa** basta PowerShell 5.1+ (preinstallato) e gli
stessi ~5 GB liberi nel profilo utente.

In entrambi i casi **non serve** la GUI né QGIS Desktop installato.

> **Perché micromamba e non `apt`?** I repo apt di qgis.org per distro vecchie
> (es. Ubuntu 20.04 "focal", ormai EOL) non hanno più build recenti.
> `conda-forge` è indipendente dalla distro, dà una QGIS aggiornata e funziona
> benissimo headless. `micromamba` è solo un binario: niente "base env" pesante,
> nessuna modifica di sistema.

---

## Passo 1 — Installare micromamba (un singolo binario)

```bash
mkdir -p ~/.local/bin
# ARCH: linux-64 su Intel/AMD, linux-aarch64 su ARM (es. Windows on ARM, Raspberry Pi)
ARCH=$([ "$(uname -m)" = "aarch64" ] && echo linux-aarch64 || echo linux-64)
curl -Ls "https://micro.mamba.pm/api/micromamba/${ARCH}/latest" \
  | tar -xj -C /tmp bin/micromamba
cp /tmp/bin/micromamba ~/.local/bin/micromamba
chmod +x ~/.local/bin/micromamba
~/.local/bin/micromamba --version
```

Assicurati che `~/.local/bin` sia nel `PATH` (di solito lo è). Verifica:

```bash
case ":$PATH:" in *":$HOME/.local/bin:"*) echo "PATH ok";; *) echo "aggiungi ~/.local/bin al PATH";; esac
```

---

## Passo 2 — Il "root prefix"

micromamba tiene tutto sotto una cartella radice (il *root prefix*): gli ambienti
in `envs/` e la cache pacchetti in `pkgs/`. La fissiamo a `~/micromamba`:

```bash
export MAMBA_ROOT_PREFIX="$HOME/micromamba"
```

L'ambiente QGIS finirà quindi in `~/micromamba/envs/qgis`. Essendo nella home, è
**a livello utente**: riutilizzabile da qualsiasi cartella/progetto.

---

## Passo 3 — Creare l'ambiente con QGIS

Scarica QGIS + GDAL + PROJ + GEOS + Qt + Python e risolve le dipendenze
(qualche minuto):

```bash
export MAMBA_ROOT_PREFIX="$HOME/micromamba"
# riproducibile: versione pinnata in environment.yml (consigliato)
~/.local/bin/micromamba create -f environment.yml -y
# oppure, per l'ultima versione disponibile su conda-forge:
# ~/.local/bin/micromamba create -n qgis -c conda-forge qgis -y
# libera la cache di download (recupera ~1.5-2 GB; l'ambiente resta intatto)
~/.local/bin/micromamba clean -a -y
```

Footprint finale tipico: **~5 GB** in `~/micromamba`.

---

## Passo 4 (opzionale) — Attivazione in ogni terminale

Per poter scrivere `micromamba activate qgis` in qualunque terminale nuovo,
inizializza la shell una volta sola (modifica un blocco gestito in `~/.bashrc`):

```bash
~/.local/bin/micromamba shell init -s bash -r ~/micromamba
# riapri il terminale, oppure: source ~/.bashrc
```

Per annullare: `micromamba shell deinit -s bash`.

Senza questo passo puoi comunque usare l'ambiente con `micromamba run` (vedi sotto).

---

## Passo 5 — Verifica

```bash
export MAMBA_ROOT_PREFIX="$HOME/micromamba"
export QT_QPA_PLATFORM=offscreen
~/.local/bin/micromamba run -n qgis qgis_process --version
~/.local/bin/micromamba run -n qgis python -c \
  "import qgis.core as q; print('QGIS', q.Qgis.QGIS_VERSION)"
```

---

## Uso

### A) Algoritmi nativi di QGIS — `qgis_process`

```bash
micromamba run -n qgis qgis_process list                 # elenca gli algoritmi
micromamba run -n qgis qgis_process help native:buffer   # parametri di uno
micromamba run -n qgis qgis_process run native:buffer -- \
  INPUT=in.shp DISTANCE=50 OUTPUT=out.gpkg
```

### B) Un file singolo `QgsProcessingAlgorithm`

Con il runner generico della skill:

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python ~/.claude/skills/qgis-headless/scripts/run_algorithm.py \
  --alg /percorso/algoritmo.py \
  --params '{"INPUT": "/percorso/input.shp", "OUTPUT": "memory:"}'
```

Nei `--params` i path esistenti diventano layer (raster o vettoriali in base
all'estensione); i parametri sono **validati prima dell'esecuzione**; con
`--project progetto.qgs` l'algoritmo può usare i layer del progetto; `@file.json`
per parametri da file. Tutte le opzioni in
[skill/qgis-headless/SKILL.md](skill/qgis-headless/SKILL.md).

### C) Ispezionare un progetto

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python examples/inspect_project.py --project progetto.qgs          # per umani
  # ... --project progetto.qgs --json | jq '.layers[].name'          # per macchine
```

### D) Renderizzare una mappa in PNG

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python examples/render_map.py \
  --input dtm.tif --qml stile.qml --input ortofoto.tif \
  --output mappa.png --width 1600
# oppure un intero progetto: --project progetto.qgs
```

### E) PyQGIS "a mano" (scheletro)

```python
import gc
from qgis.core import QgsApplication

def lavoro():
    # ... codice PyQGIS: layer, algoritmi, ... (tenere qui i riferimenti
    # ai layer: devono essere rilasciati PRIMA di exitQgis, vedi sotto)
    ...

QgsApplication.setPrefixPath("/home/UTENTE/micromamba/envs/qgis", True)
app = QgsApplication([], False)   # False = niente GUI
app.initQgis()
try:
    lavoro()
finally:
    gc.collect()      # rilascia i layer GDAL/OGR prima dello smontaggio
    app.exitQgis()    # altrimenti: segfault all'uscita (vedi Risoluzione problemi)
```

Esegui con: `QT_QPA_PLATFORM=offscreen micromamba run -n qgis python -u script.py`
(`-u` = stdout non bufferizzato: i print compaiono anche se lo script va in errore).

---

## Manutenzione

```bash
# aggiornare QGIS alla versione pinnata più recente: modifica la versione in
# environment.yml, poi ricrea l'ambiente
micromamba env remove -n qgis -y && bash setup.sh
# oppure aggiornamento libero all'ultima di conda-forge
micromamba update -n qgis -c conda-forge qgis -y
# liberare la cache
micromamba clean -a -y
# spazio occupato
du -sh ~/micromamba
# rimuovere l'ambiente
micromamba env remove -n qgis -y
```

---

## Risoluzione problemi

| Sintomo | Causa / Soluzione |
|---|---|
| `qt.qpa.plugin: could not load the Qt platform plugin "xcb"` | Manca l'offscreen: `export QT_QPA_PLATFORM=offscreen`. |
| `QStandardPaths: wrong permissions on runtime directory /mnt/wslg/...` | Innocuo (warning di WSLg), si può ignorare. |
| Nessun output quando si fa `| grep`/`| tail` e lo script termina male | Buffering: usa `python -u`. |
| `micromamba: command not found` | `~/.local/bin` non nel PATH, o usa il path assoluto `~/.local/bin/micromamba`. |
| `Could not find conda environment: qgis` | Manca `MAMBA_ROOT_PREFIX=$HOME/micromamba`, oppure l'env non è creato (Passo 3). |
| Errori PROJ/CRS | Di norma assenti: la build conda-forge porta i propri dati PROJ. |
| Segfault **all'uscita** dopo che lo script ha finito (exit 139 su Linux, `0xC0000005` su Windows) | Layer GDAL/OGR ancora referenziati quando `exitQgis()` smonta il provider registry. Rilasciarli prima: fai il lavoro in una funzione separata e chiama `gc.collect()` prima di `app.exitQgis()` (vedi `examples/hello_qgis.py`). |

---

## Note

- Questo QGIS è **separato** da un eventuale QGIS Desktop su Windows: profili,
  plugin e impostazioni non sono condivisi. Per riprodurre comportamenti
  specifici del desktop, usare invece il server MCP (`qgis_mcp_plugin`).
- GUI in WSL: con Windows 11 (WSLg) si potrebbe anche avviare la QGIS desktop
  grafica, ma per esecuzione/test headless non serve.
- Percorsi: da WSL usa percorsi nativi `/home/...`. Solo se piloti la QGIS di
  *Windows* (via MCP) servono i percorsi UNC `\\wsl.localhost\<distro>\home\...`.
