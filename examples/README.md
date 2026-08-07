# Esempi

Smoke test e utility headless per verificare che l'ambiente QGIS funzioni.

## Dati

- `data/sample.geojson` — 3 piccoli poligoni (EPSG:4326), nessuna dipendenza esterna.
- `data/sample_points.geojson` — punti in EPSG:3003 per gli esempi Verto Online.
- `data/sample_points_3003.csv` — gli stessi punti in CSV, per il batch Verto.

---

## 1. Smoke test PyQGIS (`hello_qgis.py`)

Carica un layer e ne stampa informazioni di base.

**WSL2/Linux:**
```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis python examples/hello_qgis.py
```

**Windows (PowerShell):**
```powershell
.\examples\hello_qgis_win.ps1
# oppure su un tuo layer:
.\examples\hello_qgis_win.ps1 -InputPath C:\dati\mio_layer.gpkg
```

Output atteso: `Feature : 3`, CRS `EPSG:4326`, i campi `id`/`nome` e
`OK: l'ambiente QGIS headless funziona.`

Su un tuo layer (WSL2/Linux):
```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python examples/hello_qgis.py --input /percorso/layer.shp
```

---

## 2. Ispezione progetto QGIS (`inspect_project.py`)

Stampa metadati del progetto e informazioni su tutti i layer (tipo, CRS,
geometria, campi, feature count).

**WSL2/Linux:**
```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python examples/inspect_project.py --project /percorso/progetto.qgs
```

**Windows (PowerShell):**
```powershell
.\examples\inspect_project_win.ps1 -Project C:\lavoro\progetto.qgs
```

Con `--json` emette un documento JSON machine-readable (stdout pulito,
pipe-abile direttamente in `jq` o altri strumenti):

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python examples/inspect_project.py --project progetto.qgs --json \
  | jq -r '.layers[] | "\(.name): \(.type), \(.crs)"'
```

---

## 3. Algoritmo nativo via `qgis_process`

Esempio: riproietta i poligoni in EPSG:32633 (UTM 33N) scrivendo un GeoPackage.

```bash
micromamba run -n qgis qgis_process run native:reprojectlayer -- \
  INPUT=examples/data/sample.geojson \
  TARGET_CRS=EPSG:32633 \
  OUTPUT=/tmp/sample_32633.gpkg
```

Per scoprire altri algoritmi: `micromamba run -n qgis qgis_process list`.

---

## 4. Verto Online (API IGM)

Esempio minimale per interrogare il servizio ufficiale IGM Verto Online da
linea di comando, senza GUI:

```bash
python examples/verto_online.py --request info
python examples/verto_online.py --from-epsg 3003 --to-epsg 6707 --coord 1500000 4640000

# batch da CSV (colonne e,n / x,y, o le prime due; delimitatore , o ;)
# con risultato scritto in un CSV (e_in,n_in,e_out,n_out):
python examples/verto_online.py --from-epsg 3003 --to-epsg 6707 \
  --csv examples/data/sample_points_3003.csv --output convertiti.csv
```

Le richieste vengono suddivise automaticamente in blocchi da 32.000 punti
(il limite del servizio), quindi il CSV può essere grande a piacere.

Lo script usa il servizio pubblico indicato da IGM e stampa richiesta e
risposta JSON complete. Per il formato ufficiale del payload vedi il repo
[`ondata/openverto`](https://github.com/ondata/openverto), che documenta e
incapsula lo stesso endpoint.

## 5. Verto Online come algoritmo Processing

Il file [`verto_processing_algorithm.py`](verto_processing_algorithm.py) è un
`QgsProcessingAlgorithm` singolo file che converte punti tramite il servizio
IGM e scrive un layer di output.

Esecuzione con il runner headless già presente nella skill:

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python ~/.claude/skills/qgis-headless/scripts/run_algorithm.py \
  --alg examples/verto_processing_algorithm.py \
  --params '{"INPUT": "examples/data/sample_points.geojson", "FROM_EPSG": 3003, "TO_EPSG": 6707, "OUTPUT": "memory:"}'
```

Nota: il file di esempio accetta solo sorgenti vettoriali di tipo punto. Il
parametro `FROM_EPSG`/`TO_EPSG` deve essere uno dei sistemi di riferimento
supportati da Verto Online (vedi `--request info` in `verto_online.py`); ad
esempio EPSG:4326 (WGS84) non è supportato come sistema di input. Il file
`data/sample_points.geojson` contiene coordinate già in EPSG:3003
(Monte Mario / Italy zone 1).

---

## 6. Algoritmo offline di esempio (`centroids_algorithm.py`)

Un `QgsProcessingAlgorithm` singolo file che calcola il centroide di ogni
feature. Non richiede rete: è l'esempio più semplice per provare il runner
generico, ed è quello usato dalla CI.

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python skill/qgis-headless/scripts/run_algorithm.py \
  --alg examples/centroids_algorithm.py \
  --params '{"INPUT": "examples/data/sample.geojson", "OUTPUT": "memory:"}'
```

Output atteso: `>>> OUTPUT: 3 features`.

---

## 7. Rendering headless (`render_map.py`)

Renderizza una mappa in PNG **senza aprire QGIS**: layer singoli (con stile QML
opzionale) oppure un intero progetto. Utile per report automatici, anteprime di
dataset, mappe generate in pipeline/CI.

```bash
# layer singolo
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python examples/render_map.py \
  --input examples/data/sample.geojson --output /tmp/mappa.png --width 800

# più layer con stile QML: gli --input sono disegnati dal primo (in cima)
# all'ultimo (in fondo), come nel pannello layer di QGIS; ogni --qml si
# abbina posizionalmente all'--input corrispondente ("-" = nessuno stile)
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python examples/render_map.py \
  --input dtm.tif --qml stile_dtm.qml \
  --input ortofoto.tif \
  --output mappa.png --width 1600

# un intero progetto (ordine layer e stili presi dal progetto)
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python examples/render_map.py --project progetto.qgs --output mappa.png
```

Opzioni utili: `--extent xmin,ymin,xmax,ymax`, `--crs EPSG:3857`,
`--height` (default: dal rapporto d'aspetto dell'extent), `--background`.
