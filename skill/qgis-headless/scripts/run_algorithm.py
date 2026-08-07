#!/usr/bin/env python3
"""
Generic headless runner for a single-file QgsProcessingAlgorithm.

Initializes QGIS without a GUI, imports an algorithm module, locates the
QgsProcessingAlgorithm subclass, and runs processAlgorithm() with parameters
given as JSON. Intended for testing/automation from WSL/Linux inside a
conda-forge QGIS environment.

Usage:
    QT_QPA_PLATFORM=offscreen micromamba run -n qgis python run_algorithm.py \
        --alg /path/to/algorithm.py \
        --params '{"INPUT": "/path/in.shp", "OUTPUT": "memory:"}'

In --params, string values that point to an existing file are loaded as map
layers (raster when the extension says so, vector otherwise); all other values
are passed through unchanged. With --project, a .qgs/.qgz project is loaded
into the processing context so algorithms can reference project layers.
"""
import argparse
import gc
import importlib.util
import inspect
import json
import os
import sys
import traceback

# Make stdout line-buffered so progress survives a crash when piped.
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

from qgis.core import (  # noqa: E402
    QgsApplication,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
)

RASTER_EXTS = {".tif", ".tiff", ".vrt", ".asc", ".img", ".jp2", ".xyz", ".nc"}


class PrintFeedback(QgsProcessingFeedback):
    def pushInfo(self, message):
        print("  ", message)

    def pushWarning(self, message):
        print("   WARN", message)

    def reportError(self, message, fatalError=False):
        print("   ERROR", message)


def load_module(path):
    spec = importlib.util.spec_from_file_location("user_alg_module", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_algorithm_class(mod, class_name=None):
    classes = [
        obj for _, obj in inspect.getmembers(mod, inspect.isclass)
        if issubclass(obj, QgsProcessingAlgorithm)
        and obj is not QgsProcessingAlgorithm
        and obj.__module__ == mod.__name__
    ]
    if class_name:
        for c in classes:
            if c.__name__ == class_name:
                return c
        raise RuntimeError(f"Class '{class_name}' not found. Available: "
                           f"{[c.__name__ for c in classes]}")
    if not classes:
        raise RuntimeError("No QgsProcessingAlgorithm subclass found in the module.")
    if len(classes) > 1:
        raise RuntimeError(f"Multiple algorithm classes found, use --class: "
                           f"{[c.__name__ for c in classes]}")
    return classes[0]


def resolve_params(raw):
    """Load existing-file string values as map layers (raster by extension,
    vector otherwise); pass through the rest."""
    resolved = {}
    for key, val in raw.items():
        if isinstance(val, str) and os.path.isfile(val):
            name = os.path.basename(val)
            if os.path.splitext(val)[1].lower() in RASTER_EXTS:
                layer = QgsRasterLayer(val, name)
            else:
                layer = QgsVectorLayer(val, name, "ogr")
            if not layer.isValid():
                raise RuntimeError(f"Invalid layer for param {key}: {val}")
            resolved[key] = layer
        else:
            resolved[key] = val
    return resolved


def _default_prefix():
    prefix = os.environ.get("CONDA_PREFIX", "")
    if prefix:
        lib = os.path.join(prefix, "Library")
        if os.path.isdir(lib):
            return lib
    return prefix


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alg", required=True, help="path to the algorithm .py")
    ap.add_argument("--params", default="{}",
                    help="JSON dict of parameters (or @file.json)")
    ap.add_argument("--class", dest="class_name", default=None,
                    help="algorithm class name (if the module has several)")
    ap.add_argument("--project", default=None,
                    help="optional .qgs/.qgz project to load into the "
                         "processing context (for algorithms that use "
                         "project layers)")
    ap.add_argument("--prefix", default=_default_prefix(),
                    help="QGIS prefix path (default: $CONDA_PREFIX, Library auto-detected on Windows)")
    ap.add_argument("--set", action="append", default=[], metavar="MOD.ATTR=VAL",
                    help="override a module attribute before running, e.g. "
                         "--set PAUSE_SECONDS=0 (value parsed as JSON, then str)")
    args = ap.parse_args()

    params_text = args.params
    if params_text.startswith("@"):
        with open(params_text[1:]) as fh:
            params_text = fh.read()
    raw_params = json.loads(params_text)

    def run():
        mod = load_module(args.alg)

        for override in args.set:
            name, _, value = override.partition("=")
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = value
            setattr(mod, name.strip(), parsed)
            print(f"override: {name.strip()} = {parsed!r}")

        alg_cls = find_algorithm_class(mod, args.class_name)
        alg = alg_cls()
        alg.initAlgorithm()
        print(f"Running: {alg.__class__.__name__}")

        ctx = QgsProcessingContext()
        if args.project:
            project = QgsProject.instance()
            if not project.read(args.project):
                raise RuntimeError(f"Cannot read project: {args.project}")
            print(f"Project loaded: {args.project} "
                  f"({len(project.mapLayers())} layers)")
            ctx.setProject(project)
        params = resolve_params(raw_params)

        ok, msg = alg.checkParameterValues(params, ctx)
        if not ok:
            raise RuntimeError(f"Invalid parameters: {msg}")

        result = alg.processAlgorithm(params, ctx, PrintFeedback())

        print("RESULT keys:", list(result.keys()))
        for key, val in result.items():
            layer = ctx.getMapLayer(val) if isinstance(val, str) else None
            if layer is not None:
                print(f">>> {key}: {layer.featureCount()} features")
            else:
                print(f">>> {key}: {val}")

    if args.prefix:
        QgsApplication.setPrefixPath(args.prefix, True)
    app = QgsApplication([], False)
    app.initQgis()
    exit_code = 0
    try:
        run()
    except Exception:
        # Print here instead of letting the exception propagate: Python
        # deletes the `except ... :` frame's exception and traceback when
        # this handler exits, which is what releases run()'s locals - and
        # every GDAL/OGR-backed layer object it created. If the exception
        # were left to propagate past exitQgis() below, those objects would
        # still be alive when the provider registry is torn down, and
        # finalizing them afterwards segfaults the interpreter on exit.
        traceback.print_exc()
        exit_code = 1
    finally:
        # release project layers and run()'s leftovers before teardown
        QgsProject.instance().clear()
        gc.collect()
        app.exitQgis()
    if exit_code:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
