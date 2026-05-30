#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse


API_BASE = "https://api.moysklad.ru/api/remap/1.2"
TOKEN = os.environ.get("MOYSKLAD_TOKEN")

if not TOKEN:
    print("MOYSKLAD_TOKEN is not set", file=sys.stderr)
    sys.exit(1)


SERVICE_BY_EXPENSE_ITEM = {
    "Логистика": "Доставка",
    "Сырье и ингредиенты": "Сырье без складского учета",
    "Закупка товаров": "Сырье без складского учета",
    "Упаковка и расходники": "Упаковка",
}
FALLBACK_SERVICE_NAME = "Нескладская закупка"


def request(method: str, path: str, payload=None):
    url = path if path.startswith("http") else f"{API_BASE}{path}"
    cmd = [
        "curl",
        "--compressed",
        "-sS",
        "--connect-timeout",
        "15",
        "--max-time",
        "90",
        "-X",
        method,
        url,
        "-H",
        f"Authorization: Bearer {TOKEN}",
        "-H",
        "Accept-Encoding: gzip",
    ]
    if payload is not None:
        cmd.extend(["-H", "Content-Type: application/json", "--data", json.dumps(payload, ensure_ascii=False)])
    for attempt in range(4):
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return json.loads(proc.stdout) if proc.stdout.strip() else {}
        if attempt == 3:
            print(proc.stderr, file=sys.stderr)
            proc.check_returncode()
        time.sleep(2 * (attempt + 1))


def fetch_all(path: str):
    rows = []
    offset = 0
    while True:
        data = request("GET", f"{path}{'&' if '?' in path else '?'}limit=100&offset={offset}")
        batch = data.get("rows", [])
        rows.extend(batch)
        if len(batch) < 100:
            return rows
        offset += 100


def href_meta(href: str, type_name: str):
    return {"meta": {"href": href, "type": type_name, "mediaType": "application/json"}}


def first_organization_href() -> str:
    rows = request("GET", "/entity/organization?limit=10").get("rows", [])
    if not rows:
        raise RuntimeError("No organizations found")
    return rows[0]["meta"]["href"]


def store_href_by_name(name: str) -> str:
    query = urllib.parse.quote(name)
    rows = request("GET", f"/entity/store?search={query}").get("rows", [])
    exact = [row for row in rows if row.get("name") == name]
    if len(exact) != 1:
        raise RuntimeError(f"Store lookup failed for {name}")
    return exact[0]["meta"]["href"]


def exact_service(name: str):
    query = urllib.parse.quote(name)
    rows = request("GET", f"/entity/service?search={query}").get("rows", [])
    exact = [row for row in rows if row.get("name") == name and not row.get("archived", False)]
    if len(exact) > 1:
        raise RuntimeError(f"Multiple services found for {name}")
    return exact[0] if exact else None


def ensure_service(name: str, execute: bool):
    existing = exact_service(name)
    if existing:
        return existing, False
    if not execute:
        return {"name": name, "meta": {"href": f"dry-run://service/{name}"}}, True
    created = request("POST", "/entity/service", {"name": name})
    return created, True


def existing_supply_by_external_code(code: str):
    query = urllib.parse.quote(f"externalCode={code}")
    rows = request("GET", f"/entity/supply?filter={query}").get("rows", [])
    if len(rows) > 1:
        raise RuntimeError(f"Multiple supplies found for externalCode={code}")
    return rows[0] if rows else None


def payment_ops(payment: dict):
    ops = payment.get("operations") or []
    if isinstance(ops, list):
        return ops
    return ops.get("rows", []) or []


def linked_unapplied_supply(payment: dict):
    ops = payment_ops(payment)
    if not ops:
        return None
    href = ((ops[0].get("meta") or {}).get("href") or "")
    if "/entity/supply/" not in href:
        return None
    supply = request("GET", href)
    if supply.get("applicable", True):
        return None
    return supply


def expense_item_name(payment: dict) -> str:
    return ((payment.get("expenseItem") or {}).get("name") or "").strip()


def choose_service_name(payment: dict) -> str:
    return SERVICE_BY_EXPENSE_ITEM.get(expense_item_name(payment), FALLBACK_SERVICE_NAME)


def closing_external_code(payment: dict) -> str:
    base = payment.get("externalCode") or payment.get("id") or payment.get("name")
    return f"virtual-close-{base}"


def closing_description(payment: dict) -> str:
    payment_name = payment.get("name") or "без номера"
    moment = (payment.get("moment") or "")[:10]
    desc = (payment.get("description") or "").replace("\n", " ").strip()
    return (
        f"Закрывающий документ по оплате {payment_name} от {moment}. "
        f"По правилу Syle факт получения считаем состоявшимся, если не отмечено обратное. "
        f"Склад не двигается. {desc}"
    ).strip()


def negative_supplier_counterparties():
    result = set()
    rows = fetch_all("/report/counterparty")
    for row in rows:
        balance = row.get("balance") or 0
        sales_sum = row.get("salesSum") or 0
        profit = row.get("profit") or 0
        if balance < 0 and sales_sum == 0 and profit == 0:
            result.add(row["counterparty"]["meta"]["href"])
    return result


def candidate_paymentouts(target_counterparties: set[str]):
    rows = fetch_all("/entity/paymentout?expand=agent,operations,expenseItem")
    out = []
    for row in rows:
        if not row.get("applicable", True):
            continue
        agent_href = ((row.get("agent") or {}).get("meta") or {}).get("href")
        if not agent_href or agent_href not in target_counterparties:
            continue
        if payment_ops(row) and not linked_unapplied_supply(row):
            continue
        out.append(row)
    return out


def build_supply_payload(payment: dict, organization_href: str, store_href: str, service_href: str):
    return {
        "moment": payment["moment"],
        "applicable": True,
        "organization": href_meta(organization_href, "organization"),
        "agent": payment["agent"],
        "store": href_meta(store_href, "store"),
        "externalCode": closing_external_code(payment),
        "description": closing_description(payment),
        "positions": [
            {
                "quantity": 1,
                "price": payment["sum"],
                "assortment": href_meta(service_href, "service"),
            }
        ],
    }


def link_payment_to_supply(payment: dict, supply: dict, execute: bool):
    payload = {
        "operations": [
            {
                "meta": supply["meta"],
                "linkedSum": payment["sum"],
            }
        ]
    }
    if not execute:
        return {"status": "would-link"}
    return request("PUT", payment["meta"]["href"], payload)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main():
    args = parse_args()
    organization_href = first_organization_href()
    store_href = store_href_by_name("Основной склад")
    target_counterparties = negative_supplier_counterparties()
    payments = candidate_paymentouts(target_counterparties)
    if args.limit is not None:
        payments = payments[: args.limit]

    results = []
    for payment in payments:
        service_name = choose_service_name(payment)
        service, service_created = ensure_service(service_name, args.execute)
        existing_supply = existing_supply_by_external_code(closing_external_code(payment))
        if existing_supply:
            supply = existing_supply
            supply_created = False
        elif not args.execute:
            supply = {
                "meta": {"href": f"dry-run://supply/{closing_external_code(payment)}", "type": "supply", "mediaType": "application/json"},
                "externalCode": closing_external_code(payment),
            }
            supply_created = True
        else:
            payload = build_supply_payload(payment, organization_href, store_href, service["meta"]["href"])
            supply = request("POST", "/entity/supply", payload)
            supply_created = True

        link_payment_to_supply(payment, supply, args.execute)
        results.append(
            {
                "payment_name": payment.get("name"),
                "counterparty": (payment.get("agent") or {}).get("name"),
                "sum_rub": round((payment.get("sum") or 0) / 100, 2),
                "expense_item": expense_item_name(payment),
                "service": service_name,
                "service_created": service_created,
                "supply_created": supply_created,
                "supply_href": supply["meta"]["href"],
            }
        )

    print(
        json.dumps(
            {
                "execute": args.execute,
                "count": len(results),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
