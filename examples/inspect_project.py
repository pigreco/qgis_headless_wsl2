#!/usr/bin/env python3
"""
inspect_project.py — Inspect a QGIS project (.qgs / .qgz) in headless mode.
Prints: project metadata, layer list with type, CRS, source, fields, feature count.

Usage (inside the 'qgis' environment):
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
    ap = argparse.ArgumentParser(description="Inspect a QGIS project headless")
    ap.add_argument("--project", required=True, help="Path to the .qgs / .qgz file")
    ap.add_argument("--prefix", default=_default_prefix(),
                    help="QGIS prefix (default: $CONDA_PREFIX, Library auto-detected on Windows)")
    ap.add_argument("--no-count", action="store_true",
                    help="Skip feature count (useful for large or remote datasets)")
    args = ap.parse_args()

    from qgis.core import Qgis, QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer

    if args.prefix:
        QgsApplication.setPrefixPath(args.prefix, True)
    app = QgsApplication([], False)
    app.initQgis()

    try:
        print("QGIS", Qgis.QGIS_VERSION, "initialized (headless)")

        project = QgsProject.instance()
        ok = project.read(args.project)
        if not ok:
            sys.exit(f"Cannot read project: {args.project}")

        crs = project.crs()
        try:
            saved_ver = project.lastSaveVersion().text()
        except Exception:
            saved_ver = "n/a"

        print(f"\n{'='*64}")
        print(f"  Project  : {os.path.basename(args.project)}")
        print(f"{'='*64}")
        print(f"  Title      : {project.title() or '(no title)'}")
        print(f"  Project CRS: {crs.authid()} – {crs.description()}")
        print(f"  Last saved : QGIS {saved_ver}")
        print(f"  File       : {project.absoluteFilePath()}")

        layers = project.mapLayers()
        print(f"\n  Total layers: {len(layers)}")

        for i, (lid, layer) in enumerate(sorted(layers.items(), key=lambda x: x[1].name()), 1):
            ltype_int = int(layer.type())
            ltype_name = LAYER_TYPE.get(ltype_int, f"type={ltype_int}")
            valid = "OK" if layer.isValid() else "INVALID"
            print(f"\n  {i}. [{valid}] {layer.name()}  ({ltype_name})")
            print(f"     CRS   : {layer.crs().authid()}")
            print(f"     Source: {layer.source()}")
            if isinstance(layer, QgsVectorLayer) and layer.isValid():
                geom_int = int(layer.geometryType())
                geom_name = GEOM_TYPE.get(geom_int, f"geom={geom_int}")
                fields = [f.name() for f in layer.fields()]
                print(f"     Geometry: {geom_name}")
                print(f"     Fields ({len(fields)}): {', '.join(fields)}")
                if not args.no_count:
                    print(f"     Features: {layer.featureCount()}")
                print(f"     Extent  : {layer.extent().toString(4)}")
            elif isinstance(layer, QgsRasterLayer) and layer.isValid():
                print(f"     Size  : {layer.width()} × {layer.height()} px, "
                      f"{layer.bandCount()} band(s)")
                print(f"     Extent: {layer.extent().toString(4)}")

        print(f"\n{'='*64}\n")

    finally:
        app.exitQgis()


if __name__ == "__main__":
    main()
