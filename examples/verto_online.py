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
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_ENDPOINT = "https://igmi.esercito.difesa.it/porta-magna/wps/volapi"
DEFAULT_USER = "openverto"
DEFAULT_KEY = "openverto"


def build_body(args: argparse.Namespace) -> dict:
    body = {
        "richiesta": args.request,
        "utente": DEFAULT_USER,
        "chiave": DEFAULT_KEY,
    }
    if args.request == "conversione":
        coords = args.coord or [(1500000.0, 4640000.0)]
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


def main() -> int:
    args = parse_args()
    body = build_body(args)

    print("Request:")
    print(json.dumps(body, indent=2, ensure_ascii=False))

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

    print("Response:")
    print(json.dumps(response, indent=2, ensure_ascii=False))

    if response.get("stato") == "errore":
        dove = response.get("dove", "")
        messaggio = response.get("messaggio", "unknown error")
        if dove:
            print(f"Verto error ({dove}): {messaggio}", file=sys.stderr)
        else:
            print(f"Verto error: {messaggio}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())