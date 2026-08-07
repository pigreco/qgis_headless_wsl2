#!/usr/bin/env python3
"""
inspect_project.py — Inspect a QGIS project (.qgs / .qgz) in headless mode.
Prints: project metadata, layer list with type, CRS, source, fields, feature count.
With --json, emits a machine-readable JSON document instead (nothing else goes
to stdout, so the output can be piped straight into jq or another tool).

Usage (inside the 'qgis' environment):
    QT_QPA_PLATFORM=offscreen micromamba run -n qgis python examples/inspect_project.py \
        --project /path/to/project.qgs [--json] [--no-count]
"""
import argparse
import gc
import json
import os
import sys
import traceback

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


def _extent(rect):
    return [rect.xMinimum(), rect.yMinimum(), rect.xMaximum(), rect.yMaximum()]


def gather(args):
    """Read the project and return a plain-dict description of it."""
    from qgis.core import Qgis, QgsProject, QgsVectorLayer, QgsRasterLayer

    project = QgsProject.instance()
    if not project.read(args.project):
        raise RuntimeError(f"Cannot read project: {args.project}")

    try:
        saved_ver = project.lastSaveVersion().text()
    except Exception:
        saved_ver = None

    crs = project.crs()
    info = {
        "qgis_version": Qgis.QGIS_VERSION,
        "project": {
            "file": project.absoluteFilePath(),
            "title": project.title() or None,
            "crs": crs.authid() or None,
            "crs_description": crs.description() or None,
            "last_saved": saved_ver,
        },
        "layers": [],
    }

    layers = project.mapLayers()
    for lid, layer in sorted(layers.items(), key=lambda x: x[1].name()):
        ltype_int = int(layer.type())
        entry = {
            "name": layer.name(),
            "type": LAYER_TYPE.get(ltype_int, f"type={ltype_int}"),
            "valid": layer.isValid(),
            "crs": layer.crs().authid() or None,
            "source": layer.source(),
        }
        if isinstance(layer, QgsVectorLayer) and layer.isValid():
            geom_int = int(layer.geometryType())
            entry["geometry"] = GEOM_TYPE.get(geom_int, f"geom={geom_int}")
            entry["fields"] = [
                {"name": f.name(), "type": f.typeName()} for f in layer.fields()
            ]
            entry["features"] = None if args.no_count else layer.featureCount()
            entry["extent"] = _extent(layer.extent())
        elif isinstance(layer, QgsRasterLayer) and layer.isValid():
            entry["width"] = layer.width()
            entry["height"] = layer.height()
            entry["bands"] = layer.bandCount()
            entry["extent"] = _extent(layer.extent())
        info["layers"].append(entry)

    # Release the project's GDAL/OGR-backed layers before exitQgis(): objects
    # still alive when the provider registry is torn down segfault on exit.
    project.clear()
    return info


def print_human(info, project_path):
    proj = info["project"]
    print("QGIS", info["qgis_version"], "initialized (headless)")
    print(f"\n{'='*64}")
    print(f"  Project  : {os.path.basename(project_path)}")
    print(f"{'='*64}")
    print(f"  Title      : {proj['title'] or '(no title)'}")
    print(f"  Project CRS: {proj['crs'] or ''} – {proj['crs_description'] or ''}")
    print(f"  Last saved : QGIS {proj['last_saved'] or 'n/a'}")
    print(f"  File       : {proj['file']}")

    print(f"\n  Total layers: {len(info['layers'])}")

    for i, entry in enumerate(info["layers"], 1):
        valid = "OK" if entry["valid"] else "INVALID"
        print(f"\n  {i}. [{valid}] {entry['name']}  ({entry['type']})")
        print(f"     CRS   : {entry['crs'] or ''}")
        print(f"     Source: {entry['source']}")
        if "geometry" in entry:
            names = [f["name"] for f in entry["fields"]]
            print(f"     Geometry: {entry['geometry']}")
            print(f"     Fields ({len(names)}): {', '.join(names)}")
            if entry["features"] is not None:
                print(f"     Features: {entry['features']}")
            ext = entry["extent"]
            print(f"     Extent  : {ext[0]:.4f},{ext[1]:.4f} : {ext[2]:.4f},{ext[3]:.4f}")
        elif "bands" in entry:
            print(f"     Size  : {entry['width']} × {entry['height']} px, "
                  f"{entry['bands']} band(s)")
            ext = entry["extent"]
            print(f"     Extent: {ext[0]:.4f},{ext[1]:.4f} : {ext[2]:.4f},{ext[3]:.4f}")

    print(f"\n{'='*64}\n")


def main():
    ap = argparse.ArgumentParser(description="Inspect a QGIS project headless")
    ap.add_argument("--project", required=True, help="Path to the .qgs / .qgz file")
    ap.add_argument("--prefix", default=_default_prefix(),
                    help="QGIS prefix (default: $CONDA_PREFIX, Library auto-detected on Windows)")
    ap.add_argument("--no-count", action="store_true",
                    help="Skip feature count (useful for large or remote datasets)")
    ap.add_argument("--json", action="store_true",
                    help="Emit machine-readable JSON on stdout instead of text")
    args = ap.parse_args()

    from qgis.core import QgsApplication

    if args.prefix:
        QgsApplication.setPrefixPath(args.prefix, True)
    app = QgsApplication([], False)
    app.initQgis()
    exit_code = 0
    try:
        info = gather(args)
        if args.json:
            json.dump(info, sys.stdout, indent=2, ensure_ascii=False)
            print()
        else:
            print_human(info, args.project)
    except Exception:
        # Catch here instead of propagating: this releases gather()'s locals
        # (the layer objects) before exitQgis(), avoiding a segfault on
        # interpreter shutdown (see run_algorithm.py for the full story).
        traceback.print_exc()
        exit_code = 1
    finally:
        gc.collect()
        app.exitQgis()
    if exit_code:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
