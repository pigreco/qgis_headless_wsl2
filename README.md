# Configurare QGIS headless in WSL2 (via micromamba)

Guida passo-passo per installare e usare **QGIS senza interfaccia grafica** in
WSL2 (Linux su Windows), per eseguire/testare algoritmi QGIS Processing e codice
PyQGIS da terminale o in automazione (CI), senza aprire il desktop.

> "Headless" = nessuna finestra. Per Qt serve un *platform plugin* offscreen:
> `export QT_QPA_PLATFORM=offscreen`.

---

## Avvio rapido (script automatico)

Per chi vuole configurarsi l'ambiente con **un solo comando** (lo script è
idempotente: non reinstalla nulla se è già presente):

```bash
git clone https://github.com/pigreco/qgis_headless_wsl2.git
cd qgis_headless_wsl2
bash setup.sh            # installa micromamba (se manca) + l'ambiente 'qgis'
# oppure, per attivare 'micromamba activate' in ogni terminale:
bash setup.sh --init
```

Al termine verifica con:

```bash
QT_QPA_PLATFORM=offscreen ~/.local/bin/micromamba run -n qgis qgis_process --version
```

Chi preferisce capire ogni passaggio può seguire la guida manuale qui sotto.

---

## Prerequisiti

- **WSL2** già attivo con una distro Linux (es. Ubuntu). Verifica da Windows:
  `wsl -l -v` (la colonna VERSION deve essere `2`).
- Connessione a Internet dentro WSL (il download è ~hundreds of MB).
- ~5 GB liberi nella home WSL (`df -h ~`).
- **Non serve** la GUI di Windows né QGIS Desktop installato.

> **Perché micromamba e non `apt`?** I repo apt di qgis.org per distro vecchie
> (es. Ubuntu 20.04 "focal", ormai EOL) non hanno più build recenti.
> `conda-forge` è indipendente dalla distro, dà una QGIS aggiornata e funziona
> benissimo headless. `micromamba` è solo un binario: niente "base env" pesante,
> nessuna modifica di sistema.

---

## Passo 1 — Installare micromamba (un singolo binario)

```bash
mkdir -p ~/.local/bin
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
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
~/.local/bin/micromamba create -n qgis -c conda-forge qgis -y
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

### C) PyQGIS "a mano" (scheletro)

```python
from qgis.core import QgsApplication
QgsApplication.setPrefixPath("/home/UTENTE/micromamba/envs/qgis", True)
app = QgsApplication([], False)   # False = niente GUI
app.initQgis()
# ... codice PyQGIS ...
app.exitQgis()
```

Esegui con: `QT_QPA_PLATFORM=offscreen micromamba run -n qgis python -u script.py`
(`-u` = stdout non bufferizzato: i print compaiono anche se lo script va in errore).

---

## Manutenzione

```bash
# aggiornare QGIS
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

---

## Note

- Questo QGIS è **separato** da un eventuale QGIS Desktop su Windows: profili,
  plugin e impostazioni non sono condivisi. Per riprodurre comportamenti
  specifici del desktop, usare invece il server MCP (`qgis_mcp_plugin`).
- GUI in WSL: con Windows 11 (WSLg) si potrebbe anche avviare la QGIS desktop
  grafica, ma per esecuzione/test headless non serve.
- Percorsi: da WSL usa percorsi nativi `/home/...`. Solo se piloti la QGIS di
  *Windows* (via MCP) servono i percorsi UNC `\\wsl.localhost\<distro>\home\...`.
