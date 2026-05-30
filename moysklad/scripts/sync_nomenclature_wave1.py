#!/usr/bin/env python3

import csv
import json
import os
import subprocess
import sys
import urllib.parse
import argparse
from pathlib import Path


API_BASE = "https://api.moysklad.ru/api/remap/1.2"
ROOT = Path(__file__).resolve().parents[2]
MASTER_CSV = ROOT / "moysklad" / "nomenclature_wave1_master_2026-05-29.csv"
MODIFICATIONS_CSV = ROOT / "moysklad" / "nomenclature_wave1_modifications_2026-05-29.csv"
STATE_DIR = ROOT / "moysklad" / "state"
STATE_FILE = STATE_DIR / "productfolders.json"


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


def delete_url(url: str):
    subprocess.run(
        [
            "curl",
            "--compressed",
            "-sS",
            "-X",
            "DELETE",
            url,
            "-H",
            f"Authorization: Bearer {TOKEN}",
            "-H",
            "Accept-Encoding: gzip",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def load_state():
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text())


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def href_meta(href: str, type_name: str):
    return {"meta": {"href": href, "type": type_name, "mediaType": "application/json"}}


def fetch_uom_href(name: str) -> str:
    query = urllib.parse.quote(f"name={name}")
    data = get_json(f"/entity/uom?filter={query}")
    rows = data.get("rows", [])
    if not rows:
        fatal(f"UOM not found: {name}")
    return rows[0]["meta"]["href"]


def folder_by_name(name: str):
    query = urllib.parse.quote(name)
    data = get_json(f"/entity/productfolder?search={query}")
    return data.get("rows", [])


def ensure_folder(path: str, state):
    if path in state:
        try:
            data = get_json(state[path]["href"])
            return data["meta"]["href"]
        except Exception:
            pass

    parent_href = None
    parent_path = ""
    for part in path.split("/"):
        full_path = f"{parent_path}/{part}".strip("/")
        if full_path in state:
            parent_href = state[full_path]["href"]
            parent_path = full_path
            continue

        matched_href = None
        for row in folder_by_name(part):
            if row.get("name") == part and row.get("pathName", "") == parent_path:
                matched_href = row["meta"]["href"]
                break

        if not matched_href:
            payload = {"name": part}
            if parent_href:
                payload["productFolder"] = href_meta(parent_href, "productfolder")
            created = post_json("/entity/productfolder", payload)
            matched_href = created["meta"]["href"]

        state[full_path] = {"href": matched_href}
        parent_href = matched_href
        parent_path = full_path

    save_state(state)
    return parent_href


def find_product_by_code(code: str):
    query = urllib.parse.quote(f"code={code}")
    data = get_json(f"/entity/product?filter={query}")
    rows = data.get("rows", [])
    if rows:
        return rows[0]
    return None


def find_service_by_code(code: str):
    query = urllib.parse.quote(f"code={code}")
    data = get_json(f"/entity/service?filter={query}")
    rows = data.get("rows", [])
    if rows:
        return rows[0]
    return None


def find_variant_by_code(code: str):
    query = urllib.parse.quote(f"code={code}")
    data = get_json(f"/entity/variant?filter={query}")
    rows = data.get("rows", [])
    if rows:
        return rows[0]
    return None


def create_assortment(row, uom_hrefs, folder_href):
    payload = {
        "name": row["name"],
        "code": row["code"],
        "uom": href_meta(uom_hrefs[row["uom"]], "uom"),
        "productFolder": href_meta(folder_href, "productfolder"),
        "description": row["notes"],
    }
    endpoint = "/entity/service" if row["type"] == "service" else "/entity/product"
    return post_json(endpoint, payload)


def update_assortment(existing, row, uom_hrefs, folder_href):
    payload = {
        "name": row["name"],
        "code": row["code"],
        "uom": href_meta(uom_hrefs[row["uom"]], "uom"),
        "productFolder": href_meta(folder_href, "productfolder"),
        "description": row["notes"],
    }
    return request("PUT", existing["meta"]["href"], payload)


def create_variant(row, parent_product_href):
    payload = {
        "product": href_meta(parent_product_href, "product"),
        "code": row["mod_code"],
        "characteristics": [
            {
                "name": row["characteristic_name"],
                "value": row["characteristic_value"],
            }
        ],
    }
    return post_json("/entity/variant", payload)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-create",
        action="store_true",
        help="Allow creating new products and variants that do not yet exist in MoySklad.",
    )
    return parser.parse_args()


def cleanup_test_entities():
    tests = [
        "/entity/product?filter=code=SYLE-PRODUCT-TEST",
        "/entity/productfolder?search=SYLE_SYNC_TEST_DO_NOT_DELETE",
        "/entity/productfolder?search=SYLE_PARENT_TEST",
        "/entity/productfolder?search=SYLE_CHILD_TEST",
    ]
    deleted = []
    for path in tests:
        rows = get_json(path).get("rows", [])
        for row in rows:
            delete_url(row["meta"]["href"])
            deleted.append(row.get("name", row["meta"]["href"]))
    return deleted


def main():
    args = parse_args()
    deleted = cleanup_test_entities()
    state = load_state()
    uom_hrefs = {"шт": fetch_uom_href("шт"), "кг": fetch_uom_href("кг")}

    created_products = []
    created_variants = []
    skipped = []
    ensured_paths = set()

    with MASTER_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        if row["wave1_status"] == "ready":
            ensured_paths.add(row["group_path"])

    for path in sorted(ensured_paths):
        ensure_folder(path, state)

    for row in rows:
        if row["wave1_status"] != "ready":
            skipped.append({"code": row["code"], "reason": "hold"})
            continue
        if row["type"] not in {"product", "service"}:
            skipped.append({"code": row["code"], "reason": f"type={row['type']}"})
            continue

        existing = find_service_by_code(row["code"]) if row["type"] == "service" else find_product_by_code(row["code"])
        folder_href = ensure_folder(row["group_path"], state)
        if existing:
            current_folder = existing.get("productFolder", {}).get("meta", {}).get("href")
            current_desc = existing.get("description") or ""
            current_name = existing.get("name")
            target_desc = row["notes"]
            if current_name != row["name"] or current_folder != folder_href or current_desc != target_desc:
                product = update_assortment(existing, row, uom_hrefs, folder_href)
                created_products.append({"code": row["code"], "name": product["name"]})
            else:
                skipped.append({"code": row["code"], "reason": "exists"})
            continue

        if not args.allow_create:
            skipped.append({"code": row["code"], "reason": "create_blocked_without_allow_create"})
            continue

        product = create_assortment(row, uom_hrefs, folder_href)
        created_products.append({"code": row["code"], "name": product["name"]})

    with MODIFICATIONS_CSV.open(newline="", encoding="utf-8") as f:
        mod_rows = list(csv.DictReader(f))

    for row in mod_rows:
        if row["wave1_status"] != "ready":
            skipped.append({"code": row["mod_code"], "reason": "hold"})
            continue

        existing = find_variant_by_code(row["mod_code"])
        if existing:
            skipped.append({"code": row["mod_code"], "reason": "exists"})
            continue

        parent = find_product_by_code(row["parent_code"])
        if not parent:
            skipped.append({"code": row["mod_code"], "reason": f"missing_parent={row['parent_code']}"})
            continue

        if not args.allow_create:
            skipped.append({"code": row["mod_code"], "reason": "create_blocked_without_allow_create"})
            continue

        variant = create_variant(row, parent["meta"]["href"])
        created_variants.append({"code": variant["code"], "name": variant["name"]})

    summary = {
        "allow_create": args.allow_create,
        "deleted_tests": deleted,
        "created_products_count": len(created_products),
        "created_products": created_products,
        "created_variants_count": len(created_variants),
        "created_variants": created_variants,
        "skipped_count": len(skipped),
        "skipped": skipped,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
