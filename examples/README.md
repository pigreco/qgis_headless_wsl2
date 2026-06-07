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
