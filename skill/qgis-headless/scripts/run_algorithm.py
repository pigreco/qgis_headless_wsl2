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

In --params, string values that point to an existing file are loaded as vector
layers; all other values are passed through unchanged.
"""
import argparse
import importlib.util
import inspect
import json
import os
import sys

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
    QgsVectorLayer,
)


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
        sys.exit(f"Class '{class_name}' not found. Available: "
                 f"{[c.__name__ for c in classes]}")
    if not classes:
        sys.exit("No QgsProcessingAlgorithm subclass found in the module.")
    if len(classes) > 1:
        sys.exit(f"Multiple algorithm classes found, use --class: "
                 f"{[c.__name__ for c in classes]}")
    return classes[0]


def resolve_params(raw):
    """Load existing-file string values as vector layers; pass through the rest."""
    resolved = {}
    for key, val in raw.items():
        if isinstance(val, str) and os.path.isfile(val):
            layer = QgsVectorLayer(val, os.path.basename(val), "ogr")
            if not layer.isValid():
                sys.exit(f"Invalid layer for param {key}: {val}")
            resolved[key] = layer
        else:
            resolved[key] = val
    return resolved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alg", required=True, help="path to the algorithm .py")
    ap.add_argument("--params", default="{}",
                    help="JSON dict of parameters (or @file.json)")
    ap.add_argument("--class", dest="class_name", default=None,
                    help="algorithm class name (if the module has several)")
    ap.add_argument("--prefix", default=os.environ.get("CONDA_PREFIX", ""),
                    help="QGIS prefix path (default: $CONDA_PREFIX)")
    ap.add_argument("--set", action="append", default=[], metavar="MOD.ATTR=VAL",
                    help="override a module attribute before running, e.g. "
                         "--set PAUSE_SECONDS=0 (value parsed as JSON, then str)")
    args = ap.parse_args()

    params_text = args.params
    if params_text.startswith("@"):
        with open(params_text[1:]) as fh:
            params_text = fh.read()
    raw_params = json.loads(params_text)

    if args.prefix:
        QgsApplication.setPrefixPath(args.prefix, True)
    app = QgsApplication([], False)
    app.initQgis()
    try:
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
        params = resolve_params(raw_params)
        result = alg.processAlgorithm(params, ctx, PrintFeedback())

        print("RESULT keys:", list(result.keys()))
        for key, val in result.items():
            layer = ctx.getMapLayer(val) if isinstance(val, str) else None
            if layer is not None:
                print(f">>> {key}: {layer.featureCount()} features")
            else:
                print(f">>> {key}: {val}")
    finally:
        app.exitQgis()


if __name__ == "__main__":
    main()
