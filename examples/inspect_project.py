#!/usr/bin/env python3
"""
inspect_project.py — Ispeziona un progetto QGIS (.qgs / .qgz) in modalità headless.
Stampa: metadati progetto, lista layer con tipo, CRS, sorgente, campi, feature count.

Uso (dentro l'ambiente 'qgis'):
    QT_QPA_PLATFORM=offscreen micromamba run -n qgis python examples/inspect_project.py \
        --project /path/to/project.qgs
"""
import argparse
import os
import sys

LAYER_TYPE = {0: "Vector", 1: "Raster", 2: "Plugin", 3: "Mesh",
              4: "VectorTile", 5: "Annotation", 6: "PointCloud"}
GEOM_TYPE  = {0: "Point", 1: "Line", 2: "Polygon", 3: "Unknown", 4: "Null"}


def _default_prefix():
    prefix = os.environ.get("CONDA_PREFIX", "")
    if prefix:
        lib = os.path.join(prefix, "Library")
        if os.path.isdir(lib):
            return lib
    return prefix


def main():
    ap = argparse.ArgumentParser(description="Ispeziona un progetto QGIS headless")
    ap.add_argument("--project", required=True, help="Percorso al file .qgs / .qgz")
    ap.add_argument("--prefix", default=_default_prefix(),
                    help="Prefix QGIS (default: $CONDA_PREFIX, Library auto-detected su Windows)")
    args = ap.parse_args()

    from qgis.core import Qgis, QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer

    if args.prefix:
        QgsApplication.setPrefixPath(args.prefix, True)
    app = QgsApplication([], False)
    app.initQgis()

    try:
        print("QGIS", Qgis.QGIS_VERSION, "inizializzato (headless)")

        project = QgsProject.instance()
        ok = project.read(args.project)
        if not ok:
            sys.exit(f"Impossibile leggere il progetto: {args.project}")

        crs = project.crs()
        try:
            saved_ver = project.lastSaveVersion().text()
        except Exception:
            saved_ver = "n/d"

        print(f"\n{'='*64}")
        print(f"  Progetto : {os.path.basename(args.project)}")
        print(f"{'='*64}")
        print(f"  Titolo       : {project.title() or '(nessun titolo)'}")
        print(f"  CRS progetto : {crs.authid()} – {crs.description()}")
        print(f"  Ultima salv. : QGIS {saved_ver}")
        print(f"  File         : {project.absoluteFilePath()}")

        layers = project.mapLayers()
        print(f"\n  Layer totali : {len(layers)}")

        for i, (lid, layer) in enumerate(layers.items(), 1):
            ltype_int = int(layer.type())
            ltype_name = LAYER_TYPE.get(ltype_int, f"type={ltype_int}")
            valid = "OK" if layer.isValid() else "NON VALIDO"
            print(f"\n  {i}. [{valid}] {layer.name()}  ({ltype_name})")
            print(f"     CRS     : {layer.crs().authid()}")
            print(f"     Sorgente: {layer.source()}")
            if isinstance(layer, QgsVectorLayer) and layer.isValid():
                geom_int = int(layer.geometryType())
                geom_name = GEOM_TYPE.get(geom_int, f"geom={geom_int}")
                fields = [f.name() for f in layer.fields()]
                print(f"     Geometria: {geom_name}")
                print(f"     Campi ({len(fields)}): {', '.join(fields)}")
                print(f"     Feature  : {layer.featureCount()}")
                print(f"     Extent   : {layer.extent().toString(4)}")
            elif isinstance(layer, QgsRasterLayer) and layer.isValid():
                print(f"     Dimensioni: {layer.width()} × {layer.height()} px, "
                      f"{layer.bandCount()} bande")
                print(f"     Extent   : {layer.extent().toString(4)}")

        print(f"\n{'='*64}\n")

    finally:
        app.exitQgis()


if __name__ == "__main__":
    main()
