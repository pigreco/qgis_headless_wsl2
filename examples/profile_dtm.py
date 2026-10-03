#!/usr/bin/env python3
"""
profile_dtm.py — Extract and plot a longitudinal profile from a DEM (raster).

Samples elevation values along a line (e.g., from SW to NE) and creates
a matplotlib chart showing elevation vs distance.

Usage (inside the 'qgis' environment):
    QT_QPA_PLATFORM=offscreen micromamba run -n qgis python examples/profile_dtm.py \
        --input etna_catania_dtm5m.tif \
        --output /tmp/profile.png
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


def extract_profile(dtm_path, num_samples=500):
    """
    Sample elevation along a SW→NE diagonal line through the DTM using GDAL.
    Returns (distances, elevations) as lists.
    """
    from osgeo import gdal
    import numpy as np

    ds = gdal.Open(dtm_path)
    if not ds:
        raise RuntimeError(f"Cannot open raster with GDAL: {dtm_path}")

    band = ds.GetRasterBand(1)
    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()  # (x0, px_width, 0, y0, 0, -px_height)

    print(f"DTM size: {width} x {height} pixels")
    print(f"Geotransform: {gt}")

    # SW to NE diagonal line (in pixel coordinates)
    distances = []
    elevations = []
    pixel_size = ((gt[1]**2 + gt[5]**2) ** 0.5)  # avg pixel size

    for i in range(num_samples):
        t = i / (num_samples - 1)  # 0.0 to 1.0
        # Pixel coordinates
        px = int(t * (width - 1))
        py = int(t * (height - 1))

        # Distance along the diagonal (in meters)
        dist_meters = (px**2 + py**2) ** 0.5 * pixel_size

        # Read pixel value
        try:
            value = band.ReadAsArray(px, py, 1, 1)[0, 0]
            elev = float(value)
        except Exception:
            elev = None

        distances.append(dist_meters / 1000)  # convert to km
        elevations.append(elev)

    return distances, elevations


def plot_profile(distances, elevations, output_path):
    """Create a matplotlib chart of the profile."""
    import matplotlib.pyplot as plt
    import numpy as np

    # Filter out None values and GDAL no-data marker (-9999)
    valid = [(d, e) for d, e in zip(distances, elevations)
             if e is not None and e > -9000]
    if not valid:
        raise RuntimeError("No valid elevation samples found")

    dists, elvs = zip(*valid)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(dists, elvs, linewidth=2.5, color="#d62728", label="Elevation")
    ax.fill_between(dists, elvs, alpha=0.25, color="#d62728")

    ax.set_xlabel("Distance along profile (km)", fontsize=11)
    ax.set_ylabel("Elevation (m)", fontsize=11)
    ax.set_title("Longitudinal Profile: Etna DTM (SW → NE diagonal)", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(loc="upper left")

    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    print(f"Profile chart saved: {output_path}")

    # Print statistics
    print(f"Elevation range: {min(elvs):.1f} – {max(elvs):.1f} m")
    print(f"Profile length: {dists[-1]:.1f} km")
    print(f"Relief (max - min): {max(elvs) - min(elvs):.1f} m")


def main():
    ap = argparse.ArgumentParser(description="Extract and plot DEM profile")
    ap.add_argument("--input", required=True, help="input raster (DEM/DTM)")
    ap.add_argument("--output", required=True, help="output PNG path")
    ap.add_argument("--samples", type=int, default=500,
                    help="number of samples along the profile (default: 500)")
    ap.add_argument("--prefix", default=_default_prefix(),
                    help="QGIS prefix (default: $CONDA_PREFIX)")
    args = ap.parse_args()

    from qgis.core import QgsApplication

    if args.prefix:
        QgsApplication.setPrefixPath(args.prefix, True)
    app = QgsApplication([], False)
    app.initQgis()
    exit_code = 0
    try:
        distances, elevations = extract_profile(args.input, args.samples)
        plot_profile(distances, elevations, args.output)
    except Exception:
        traceback.print_exc()
        exit_code = 1
    finally:
        gc.collect()
        app.exitQgis()
    if exit_code:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
