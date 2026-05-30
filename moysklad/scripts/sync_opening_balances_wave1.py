#!/usr/bin/env python3

import csv
import json
import os
import subprocess
import sys
import urllib.parse
from pathlib import Path


API_BASE = "https://api.moysklad.ru/api/remap/1.2"
ROOT = Path(__file__).resolve().parents[2]
BALANCE_CSV = ROOT / "moysklad" / "opening_balances_wave1_2026-05-29.csv"
DOC_NAME = "OB-WAVE1-PARTIAL-2026-05-29"
DOC_DESCRIPTION = (
    "Стартовое оприходование по инвентаризации от 26.05.2026 "
    "с корректировками на 28.05.2026."
)
DOC_MOMENT = "2026-05-29 00:00:00"


def fatal(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


TOKEN = os.environ.get("MOYSKLAD_TOKEN")
if not TOKEN:
    fatal("MOYSKLAD_TOKEN is not set")


def request(method: str, path: str, payload=None):
    url = path if path.startswith("http") else f"{API_BASE}{path}"
    cmd = [
        "curl",
        "--compressed",
        "-sS",
        "-X",
        method,
        url,
        "-H",
        f"Authorization: Bearer {TOKEN}",
        "-H",
        "Accept-Encoding: gzip",
    ]
    if payload is not None:
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(payload, ensure_ascii=False)])
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def get_json(path: str):
    return request("GET", path)


def post_json(path: str, payload):
    return request("POST", path, payload)


def href_meta(href: str, type_name: str):
    return {"meta": {"href": href, "type": type_name, "mediaType": "application/json"}}


def fetch_single(path: str, entity_name: str):
    rows = get_json(path).get("rows", [])
    if not rows:
        fatal(f"{entity_name} not found for {path}")
    if len(rows) > 1:
        fatal(f"Multiple {entity_name} rows returned for {path}")
    return rows[0]


def first_organization_href() -> str:
    rows = get_json("/entity/organization?limit=10").get("rows", [])
    if not rows:
        fatal("No organizations found")
    return rows[0]["meta"]["href"]


def store_href_by_name(name: str) -> str:
    query = urllib.parse.quote(name)
    rows = get_json(f"/entity/store?search={query}").get("rows", [])
    exact = [row for row in rows if row.get("name") == name]
    if len(exact) != 1:
        fatal(f"Store lookup failed for {name}")
    return exact[0]["meta"]["href"]


def product_href_by_code(code: str) -> str:
    query = urllib.parse.quote(f"code={code}")
    row = fetch_single(f"/entity/product?filter={query}", f"product {code}")
    return row["meta"]["href"]


def existing_enter():
    query = urllib.parse.quote(f"name={DOC_NAME}")
    rows = get_json(f"/entity/enter?filter={query}").get("rows", [])
    if not rows:
        return None
    if len(rows) > 1:
        fatal(f"Multiple enter documents found for {DOC_NAME}")
    return rows[0]


def load_rows():
    with BALANCE_CSV.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_payload():
    rows = load_rows()
    if not rows:
        fatal(f"No balance rows in {BALANCE_CSV}")

    store_name = rows[0]["store_name"]
    store_href = store_href_by_name(store_name)
    organization_href = first_organization_href()
    positions = []

    for row in rows:
        if row["store_name"] != store_name:
            fatal("Multiple stores in opening balance CSV are not supported in one document")
        positions.append(
            {
                "quantity": float(row["quantity"]),
                "price": 0,
                "assortment": href_meta(product_href_by_code(row["code"]), "product"),
            }
        )

    return {
        "name": DOC_NAME,
        "description": DOC_DESCRIPTION,
        "moment": DOC_MOMENT,
        "applicable": True,
        "organization": href_meta(organization_href, "organization"),
        "store": href_meta(store_href, "store"),
        "positions": positions,
    }


def main():
    execute = "--execute" in sys.argv
    payload = build_payload()
    existing = existing_enter()

    if existing:
        print(json.dumps({"status": "exists", "name": existing.get("name"), "href": existing["meta"]["href"]}, ensure_ascii=False, indent=2))
        return

    if not execute:
        preview = {
            "status": "dry-run",
            "name": payload["name"],
            "moment": payload["moment"],
            "positions": len(payload["positions"]),
            "first_codes": [row["code"] for row in load_rows()[:5]],
        }
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return

    created = post_json("/entity/enter", payload)
    print(
        json.dumps(
            {
                "status": "created",
                "name": created.get("name"),
                "href": created["meta"]["href"],
                "positions": created.get("positions", {}).get("meta", {}).get("size"),
                "moment": created.get("moment"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
