#!/usr/bin/env python3
"""
verto_online.py - minimal headless demo for the IGM Verto Online API.

This example sends a JSON POST to the official Verto endpoint and prints the
JSON response. It is intentionally dependency-free so it can run inside the
same WSL/headless environment used by the rest of this repository.

Usage:
    python examples/verto_online.py --request info
    python examples/verto_online.py --from-epsg 3003 --to-epsg 6707 \
        --coord 1500000 4640000
    # batch from CSV (columns e,n / x,y or first two columns), result to CSV
    python examples/verto_online.py --from-epsg 3003 --to-epsg 6707 \
        --csv punti.csv --output convertiti.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_ENDPOINT = "https://igmi.esercito.difesa.it/porta-magna/wps/volapi"
DEFAULT_USER = "openverto"
DEFAULT_KEY = "openverto"
MAX_COORD = 32000  # max points per request accepted by the service


def _is_float(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def read_csv_coords(path: str) -> list[tuple[float, float]]:
    """Read (e, n) pairs from a CSV file.

    Column detection: if the first row is not numeric it is treated as a
    header and the columns named e/n, est/nord or x/y (case-insensitive) are
    used; otherwise the first two columns are taken as E and N.
    """
    with open(path, newline="", encoding="utf-8-sig") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        rows = [row for row in csv.reader(fh, dialect)
                if row and any(cell.strip() for cell in row)]
    if not rows:
        sys.exit(f"Empty CSV: {path}")

    e_idx, n_idx, start = 0, 1, 0
    first = [cell.strip().lower() for cell in rows[0]]
    if len(first) < 2 or not all(_is_float(c) for c in rows[0][:2]):
        start = 1
        for e_name, n_name in (("e", "n"), ("est", "nord"), ("x", "y")):
            if e_name in first and n_name in first:
                e_idx, n_idx = first.index(e_name), first.index(n_name)
                break

    coords = []
    for lineno, row in enumerate(rows[start:], start + 1):
        try:
            coords.append((float(row[e_idx]), float(row[n_idx])))
        except (ValueError, IndexError):
            sys.exit(f"{path}: row {lineno}: invalid coordinates: {row}")
    if not coords:
        sys.exit(f"No coordinates found in {path}")
    return coords


def write_csv_coords(path: str, in_coords: list, out_coords: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["e_in", "n_in", "e_out", "n_out"])
        for (e_in, n_in), (e_out, n_out) in zip(in_coords, out_coords):
            writer.writerow([e_in, n_in, e_out, n_out])


def build_body(args: argparse.Namespace, coords: list) -> dict:
    body = {
        "richiesta": args.request,
        "utente": DEFAULT_USER,
        "chiave": DEFAULT_KEY,
    }
    if args.request == "conversione":
        body.update(
            {
                "inEpsg": args.from_epsg,
                "outEpsg": args.to_epsg,
                "coordinate": [{"e": e, "n": n} for e, n in coords],
            }
        )
    return body


def post_json(endpoint: str, body: dict, timeout: float) -> dict:
    payload = json.dumps(body).encode("utf-8")
    request = Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "qgis-headless-verto-demo",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    # The Verto endpoint sometimes prepends a debug log line (e.g. an SQL
    # INSERT statement) before the actual JSON body, so parse from the
    # first '{' rather than assuming the whole body is valid JSON.
    start = raw.find("{")
    if start == -1:
        raise json.JSONDecodeError("no JSON object found in response", raw, 0)
    return json.loads(raw[start:])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--request",
        choices=("info", "conversione"),
        default="conversione",
        help="tipo di richiesta Verto da inviare",
    )
    parser.add_argument(
        "--from-epsg",
        type=int,
        default=3003,
        help="EPSG di origine per la conversione",
    )
    parser.add_argument(
        "--to-epsg",
        type=int,
        default=6707,
        help="EPSG di destinazione per la conversione",
    )
    parser.add_argument(
        "--coord",
        action="append",
        nargs=2,
        type=float,
        metavar=("E", "N"),
        help="coppia di coordinate e n; ripetibile",
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="CSV con le coordinate da convertire (colonne e,n / x,y "
             "oppure le prime due colonne); alternativa a --coord",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="scrive il risultato in questo CSV (e_in,n_in,e_out,n_out) "
             "invece di stampare la risposta JSON",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help="endpoint API Verto (default: quello ufficiale IGM)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="timeout HTTP in secondi",
    )
    return parser.parse_args()


def _check_error(response: dict) -> str | None:
    if response.get("stato") == "errore":
        dove = response.get("dove", "")
        messaggio = response.get("messaggio", "unknown error")
        return (f"Verto error ({dove}): {messaggio}" if dove
                else f"Verto error: {messaggio}")
    return None


def main() -> int:
    args = parse_args()

    if args.csv and args.coord:
        sys.exit("Use either --coord or --csv, not both")

    if args.request == "info" or args.csv is None:
        coords = [tuple(c) for c in (args.coord or [(1500000.0, 4640000.0)])]
    else:
        coords = read_csv_coords(args.csv)

    # Historic behavior (full request/response JSON) for small interactive
    # runs; compact progress lines for batch (--csv / --output) runs.
    verbose = args.csv is None and args.output is None

    converted: list[tuple[float, float]] = []
    total_chunks = ((len(coords) + MAX_COORD - 1) // MAX_COORD
                    if args.request == "conversione" else 1)
    for index in range(total_chunks):
        chunk = coords[index * MAX_COORD:(index + 1) * MAX_COORD]
        body = build_body(args, chunk)

        if verbose:
            print("Request:")
            print(json.dumps(body, indent=2, ensure_ascii=False))
        else:
            print(f"Chunk {index + 1}/{total_chunks}: "
                  f"sending {len(chunk)} coordinates ...")

        try:
            response = post_json(args.endpoint, body, args.timeout)
        except HTTPError as exc:
            print(f"HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
            return 2
        except URLError as exc:
            print(f"Network error: {exc.reason}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON response: {exc}", file=sys.stderr)
            return 2

        if verbose:
            print("Response:")
            print(json.dumps(response, indent=2, ensure_ascii=False))

        error = _check_error(response)
        if error:
            print(error, file=sys.stderr)
            return 1

        if args.request == "conversione":
            output = response.get("coordinate", [])
            if len(output) != len(chunk):
                print(f"Verto returned {len(output)} coordinates for "
                      f"{len(chunk)} input points", file=sys.stderr)
                return 1
            converted.extend(
                (float(item["e"]), float(item["n"])) for item in output
            )

    if args.request == "conversione" and args.output:
        write_csv_coords(args.output, coords, converted)
        print(f"Written {len(converted)} converted coordinates to {args.output}")
    elif args.request == "conversione" and not verbose:
        print(json.dumps([{"e": e, "n": n} for e, n in converted],
                         indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())