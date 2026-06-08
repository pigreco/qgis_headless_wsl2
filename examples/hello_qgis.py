#!/usr/bin/env python3
"""
hello_qgis.py — smoke test minimale di PyQGIS headless.

Inizializza QGIS senza GUI, carica un layer vettoriale e ne stampa
informazioni di base. Serve a verificare che l'ambiente sia configurato
correttamente.

Uso (dentro l'ambiente 'qgis'):
    QT_QPA_PLATFORM=offscreen micromamba run -n qgis python examples/hello_qgis.py
    # oppure indicando un altro layer:
    ... python examples/hello_qgis.py --input /percorso/layer.shp
"""
import argparse
import os

from qgis.core import Qgis, QgsApplication, QgsVectorLayer

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT = os.path.join(HERE, "data", "sample.geojson")


def _default_prefix():
    prefix = os.environ.get("CONDA_PREFIX", "")
    if prefix:
        lib = os.path.join(prefix, "Library")
        if os.path.isdir(lib):
            return lib
    return prefix


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=DEFAULT_INPUT, help="layer vettoriale da leggere")
    ap.add_argument("--prefix", default=_default_prefix(),
                    help="prefix QGIS (default: $CONDA_PREFIX, con auto-detect Library su Windows)")
    args = ap.parse_args()

    # Inizializza QGIS senza interfaccia.
    if args.prefix:
        QgsApplication.setPrefixPath(args.prefix, True)
    app = QgsApplication([], False)
    app.initQgis()
    try:
        print("QGIS", Qgis.QGIS_VERSION, "inizializzato (headless)")
        layer = QgsVectorLayer(args.input, "sample", "ogr")
        if not layer.isValid():
            raise SystemExit(f"Layer non valido: {args.input}")

        print("Input   :", args.input)
        print("Feature :", layer.featureCount())
        print("CRS     :", layer.crs().authid())
        print("Extent  :", layer.extent().toString(4))
        print("Campi   :", [f.name() for f in layer.fields()])
        print("\nPrime feature:")
        for feat in list(layer.getFeatures())[:5]:
            print("  -", dict(zip(layer.fields().names(), feat.attributes())))
        print("\nOK: l'ambiente QGIS headless funziona.")
    finally:
        app.exitQgis()


if __name__ == "__main__":
    main()
