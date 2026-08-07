#!/usr/bin/env python3
"""
render_map.py — Render a map to PNG in headless mode (no GUI).

Loads one or more layers (or a whole .qgs/.qgz project), optionally applies
QML styles, and renders a PNG with QgsMapRendererParallelJob. This is the
missing piece after headless processing: the full QGIS cycle — data,
analysis, final map — without ever opening the desktop.

Usage (inside the 'qgis' environment):
    # single layer
    QT_QPA_PLATFORM=offscreen micromamba run -n qgis python examples/render_map.py \
        --input examples/data/sample.geojson --output /tmp/map.png --width 800

    # two layers with a QML style: inputs are drawn top-first (like the QGIS
    # layer panel); --qml pairs positionally with --input ("-" = no style)
    ... python examples/render_map.py \
        --input etna_catania_dtm5m.tif --qml etna_catania_dtm5m.qml \
        --input etna_catania_rgb.tif \
        --output etna.png --width 1600

    # a whole project (layer order and styles come from the project)
    ... python examples/render_map.py --project progetto.qgs --output map.png
"""
import argparse
import gc
import os
import sys
import traceback


def _default_prefix():
    prefix = os.environ.get("CONDA_PREFIX", "")
    if prefix:
        lib = os.path.join(prefix, "Library")
        if os.path.isdir(lib):
            return lib
    return prefix


RASTER_EXTS = {".tif", ".tiff", ".vrt", ".asc", ".img", ".jp2", ".xyz", ".nc"}


def load_layer(path, qml=None):
    from qgis.core import QgsRasterLayer, QgsVectorLayer

    name = os.path.basename(path)
    if os.path.splitext(path)[1].lower() in RASTER_EXTS:
        layer = QgsRasterLayer(path, name)
    else:
        layer = QgsVectorLayer(path, name, "ogr")
    if not layer.isValid():
        raise RuntimeError(f"Invalid layer: {path}")
    if qml:
        _, ok = layer.loadNamedStyle(qml)
        if not ok:
            raise RuntimeError(f"Cannot apply QML style {qml} to {path}")
        print(f"Style applied: {qml} -> {name}")
    return layer


def collect_layers(args):
    """Return (layers, dest_crs). Layers are ordered top-first."""
    from qgis.core import QgsCoordinateReferenceSystem, QgsProject

    if args.project:
        project = QgsProject.instance()
        if not project.read(args.project):
            raise RuntimeError(f"Cannot read project: {args.project}")
        layers = list(project.layerTreeRoot().layerOrder())
        if not layers:
            raise RuntimeError("The project contains no layers")
        crs = project.crs() if project.crs().isValid() else layers[0].crs()
        print(f"Project loaded: {args.project} ({len(layers)} layers)")
        return layers, crs

    qmls = list(args.qml or [])
    qmls += [None] * (len(args.input) - len(qmls))
    layers = [load_layer(path, None if qml in (None, "-") else qml)
              for path, qml in zip(args.input, qmls)]
    if args.crs:
        crs = QgsCoordinateReferenceSystem(args.crs)
        if not crs.isValid():
            raise RuntimeError(f"Invalid CRS: {args.crs}")
    else:
        crs = layers[0].crs()
    return layers, crs


def combined_extent(layers, dest_crs):
    from qgis.core import QgsCoordinateTransform, QgsProject, QgsRectangle

    extent = QgsRectangle()
    extent.setNull()
    ctx = QgsProject.instance().transformContext()
    for layer in layers:
        rect = layer.extent()
        if layer.crs() != dest_crs:
            rect = QgsCoordinateTransform(layer.crs(), dest_crs, ctx) \
                .transformBoundingBox(rect)
        extent.combineExtentWith(rect)
    if extent.isEmpty():
        raise RuntimeError("Empty combined extent: nothing to render")
    return extent


def render(args):
    from qgis.core import QgsMapRendererParallelJob, QgsMapSettings, QgsRectangle
    from qgis.PyQt.QtCore import QSize
    from qgis.PyQt.QtGui import QColor

    layers, dest_crs = collect_layers(args)

    if args.extent:
        parts = [float(v) for v in args.extent.split(",")]
        if len(parts) != 4:
            raise RuntimeError("--extent must be xmin,ymin,xmax,ymax")
        extent = QgsRectangle(parts[0], parts[1], parts[2], parts[3])
    else:
        extent = combined_extent(layers, dest_crs)

    width = args.width
    height = args.height or max(1, round(width * extent.height() / extent.width()))

    settings = QgsMapSettings()
    settings.setLayers(layers)
    settings.setDestinationCrs(dest_crs)
    settings.setExtent(extent)
    settings.setOutputSize(QSize(width, height))
    settings.setBackgroundColor(QColor(args.background))

    print(f"Rendering {len(layers)} layer(s), {width}x{height} px, "
          f"CRS {dest_crs.authid()} ...")
    job = QgsMapRendererParallelJob(settings)
    job.start()
    job.waitForFinished()

    image = job.renderedImage()
    if image.isNull():
        raise RuntimeError("Rendering produced an empty image")
    if not image.save(args.output):
        raise RuntimeError(f"Cannot write {args.output}")
    print(f"Saved: {args.output} ({os.path.getsize(args.output)} bytes)")


def main():
    ap = argparse.ArgumentParser(description="Render a map to PNG headless")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", action="append", default=None,
                     help="layer to draw (repeatable; first = on top, "
                          "like the QGIS layer panel)")
    src.add_argument("--project", default=None,
                     help=".qgs/.qgz project to render (order and styles "
                          "come from the project)")
    ap.add_argument("--qml", action="append", default=None,
                    help="QML style, paired positionally with --input "
                         "('-' = no style for that layer)")
    ap.add_argument("--output", required=True, help="output PNG path")
    ap.add_argument("--width", type=int, default=1200, help="width in px")
    ap.add_argument("--height", type=int, default=0,
                    help="height in px (default: from extent aspect ratio)")
    ap.add_argument("--extent", default=None,
                    help="xmin,ymin,xmax,ymax in the destination CRS "
                         "(default: combined layer extent)")
    ap.add_argument("--crs", default=None,
                    help="destination CRS, e.g. EPSG:3857 "
                         "(default: first layer / project CRS)")
    ap.add_argument("--background", default="white",
                    help="background color (name or #RRGGBB)")
    ap.add_argument("--prefix", default=_default_prefix(),
                    help="QGIS prefix (default: $CONDA_PREFIX, Library "
                         "auto-detected on Windows)")
    args = ap.parse_args()

    from qgis.core import QgsApplication, QgsProject

    if args.prefix:
        QgsApplication.setPrefixPath(args.prefix, True)
    app = QgsApplication([], False)
    app.initQgis()
    exit_code = 0
    try:
        render(args)
    except Exception:
        # Catch here instead of propagating: releases render()'s locals (the
        # layers) before exitQgis(), avoiding the segfault on interpreter
        # shutdown (see README, "Risoluzione problemi").
        traceback.print_exc()
        exit_code = 1
    finally:
        QgsProject.instance().clear()
        gc.collect()
        app.exitQgis()
    if exit_code:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
