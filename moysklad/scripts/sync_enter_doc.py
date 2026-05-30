#!/usr/bin/env python3

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path


API_BASE = "https://api.moysklad.ru/api/remap/1.2"


def fatal(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


TOKEN = os.environ.get("MOYSKLAD_TOKEN")
if not TOKEN:
    fatal("MOYSKLAD_TOKEN is not set")


def request(method: str, path: str, payload=None, allow_empty: bool = False):
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
    if allow_empty and not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def get_json(path: str):
    return request("GET", path)


def post_json(path: str, payload):
    return request("POST", path, payload)


def normalize_moment(value: str) -> str:
    # MoySklad expects a space separator, not ISO-8601 "T".
    return value.replace("T", " ")


def href_meta(href: str, type_name: str):
    return {"meta": {"href": href, "type": type_name, "mediaType": "application/json"}}


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


def entity_href(entity_type: str, code: str) -> str:
    endpoint = "/entity/product" if entity_type == "product" else "/entity/variant"
    query = urllib.parse.quote(f"code={code}")
    rows = get_json(f"{endpoint}?filter={query}").get("rows", [])
    if len(rows) != 1:
        fatal(f"Lookup failed for {entity_type} {code}")
    return rows[0]["meta"]["href"]


def existing_enter(doc_name: str):
    query = urllib.parse.quote(f"name={doc_name}")
    rows = get_json(f"/entity/enter?filter={query}").get("rows", [])
    if not rows:
        return None
    if len(rows) > 1:
        fatal(f"Multiple enter documents found for {doc_name}")
    return rows[0]


def validate_description(description: str, allow_non_russian: bool) -> None:
    normalized = " ".join(description.split())
    if not normalized:
        fatal("Description must not be empty")
    if not allow_non_russian and not re.search(r"[А-Яа-яЁё]", normalized):
        fatal(
            "Description for enter document must contain Russian text. "
            "Use a short factual Russian comment or pass --allow-non-russian-description."
        )
    if not allow_non_russian and re.search(r"[A-Za-z]", normalized):
        fatal(
            "Description for enter document must stay in Russian without English words. "
            "If an exception is really needed, pass --allow-non-russian-description."
        )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--moment", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--allow-non-russian-description", action="store_true")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    validate_description(args.description, args.allow_non_russian_description)
    rows = list(csv.DictReader(Path(args.csv).open(newline="", encoding="utf-8")))
    if not rows:
        fatal("No rows in enter CSV")

    store_name = rows[0]["store_name"]
    payload = {
        "name": args.name,
        "moment": normalize_moment(args.moment),
        "description": args.description,
        "applicable": True,
        "organization": href_meta(first_organization_href(), "organization"),
        "store": href_meta(store_href_by_name(store_name), "store"),
        "positions": [],
    }
    for row in rows:
        entity_type = row["entity_type"]
        payload["positions"].append(
            {
                "quantity": float(row["quantity"]),
                "price": 0,
                "assortment": href_meta(entity_href(entity_type, row["code"]), entity_type),
            }
        )

    existing = existing_enter(args.name)
    if existing:
        print(json.dumps({"status": "exists", "name": existing.get("name"), "href": existing["meta"]["href"]}, ensure_ascii=False, indent=2))
        return

    if not args.execute:
        print(json.dumps({"status": "dry-run", "name": args.name, "positions": len(payload["positions"])}, ensure_ascii=False, indent=2))
        return

    created = post_json("/entity/enter", payload)
    if "meta" not in created:
        fatal(json.dumps(created, ensure_ascii=False, indent=2))
    print(
        json.dumps(
            {
                "status": "created",
                "name": created.get("name"),
                "href": created["meta"]["href"],
                "moment": created.get("moment"),
                "positions": created.get("positions", {}).get("meta", {}).get("size"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
