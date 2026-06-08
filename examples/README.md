# Esempi

Smoke test per verificare che l'ambiente QGIS headless funzioni.

## Dati

- `data/sample.geojson` — 3 piccoli poligoni (EPSG:4326), nessuna dipendenza esterna.

## 1. PyQGIS minimale

Carica un layer e ne stampa informazioni di base:

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis python examples/hello_qgis.py
```

Output atteso: `Feature : 3`, CRS `EPSG:4326`, i campi `id`/`nome` e
`OK: l'ambiente QGIS headless funziona.`

Su un tuo layer:

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python examples/hello_qgis.py --input /percorso/layer.shp
```

## 2. Algoritmo nativo via qgis_process

Esempio: riproietta i poligoni in EPSG:32633 (UTM 33N) scrivendo un GeoPackage.

```bash
micromamba run -n qgis qgis_process run native:reprojectlayer -- \
  INPUT=examples/data/sample.geojson \
  TARGET_CRS=EPSG:32633 \
  OUTPUT=/tmp/sample_32633.gpkg
```

Per scoprire altri algoritmi: `micromamba run -n qgis qgis_process list`.

## 3. Verto Online (API IGM)

Esempio minimale per interrogare il servizio ufficiale IGM Verto Online da
linea di comando, senza GUI:

```bash
python examples/verto_online.py --request info
python examples/verto_online.py --from-epsg 3003 --to-epsg 6707 --coord 1500000 4640000
```

Lo script usa il servizio pubblico indicato da IGM e stampa richiesta e
risposta JSON complete. Per il formato ufficiale del payload vedi il repo
[`ondata/openverto`](https://github.com/ondata/openverto), che documenta e
incapsula lo stesso endpoint.

## 4. Verto Online come algoritmo Processing

Il file [`verto_processing_algorithm.py`](verto_processing_algorithm.py) è un
`QgsProcessingAlgorithm` singolo file che converte punti tramite il servizio
IGM e scrive un layer di output.

Esecuzione con il runner headless già presente nella skill:

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python ~/.claude/skills/qgis-headless/scripts/run_algorithm.py \
  --alg examples/verto_processing_algorithm.py \
  --params '{"INPUT": "examples/data/sample_points.geojson", "FROM_EPSG": 4326, "TO_EPSG": 6707, "OUTPUT": "memory:"}'
```

Nota: il file di esempio accetta solo sorgenti vettoriali di tipo punto.
