#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import time


API_BASE = "https://api.moysklad.ru/api/remap/1.2"
TOKEN = os.environ.get("MOYSKLAD_TOKEN")

if not TOKEN:
    print("MOYSKLAD_TOKEN is not set", file=sys.stderr)
    sys.exit(1)


def request(method: str, path: str):
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
    for attempt in range(4):
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return json.loads(proc.stdout) if proc.stdout.strip() else {}
        if attempt == 3:
            print(proc.stderr, file=sys.stderr)
            proc.check_returncode()
        time.sleep(2 * (attempt + 1))


def fetch_all(endpoint: str):
    rows = []
    offset = 0
    while True:
        data = request("GET", f"/entity/{endpoint}?limit=100&offset={offset}&expand=operations,expenseItem")
        batch = data.get("rows", [])
        rows.extend(batch)
        if len(batch) < 100:
            return rows
        offset += 100


def report_rows():
    rows = []
    offset = 0
    while True:
        data = request("GET", f"/report/counterparty?limit=100&offset={offset}")
        batch = data.get("rows", [])
        rows.extend(batch)
        if len(batch) < 100:
            return rows
        offset += 100


def rub(value) -> float:
    return round((value or 0) / 100, 2)


def op_rows(payment: dict):
    ops = payment.get("operations") or []
    if isinstance(ops, list):
        return ops
    return ops.get("rows", []) or []


def fetch_supply_state(href: str, cache: dict):
    if href not in cache:
        cache[href] = request("GET", href)
    return cache[href]


def classify_payment(payment: dict, supply_cache: dict):
    ops = op_rows(payment)
    if not ops:
        return "no_operations", "Создать закрывающую приемку/поставку и привязать платеж."

    first = ops[0]
    href = (first.get("meta") or {}).get("href", "")
    if "/entity/supply/" in href:
        supply = fetch_supply_state(href, supply_cache)
        if not supply.get("applicable", True):
            return "linked_unapplied_supply", "Платеж привязан к непроведенной приемке/поставке. Провести или заменить закрывающий документ."
        return "linked_applied_supply", "Связка есть. Проверить, нет ли у контрагента других незакрытых платежей."
    return "linked_other", "Проверить тип связанной операции и корректность закрытия."


def main():
    payments = [
        p for p in fetch_all("paymentout")
        if p.get("applicable", True) and (p.get("sum") or 0) > 0
    ]
    report = [r for r in report_rows() if (r.get("balance") or 0) < 0]
    supply_cache = {}

    payment_by_counterparty = {}
    for payment in payments:
        href = ((payment.get("agent") or {}).get("meta") or {}).get("href")
        if not href:
            continue
        payment_by_counterparty.setdefault(href, []).append(payment)

    output = []
    for row in sorted(report, key=lambda item: item.get("balance") or 0):
        counterparty = row["counterparty"]
        href = counterparty["meta"]["href"]
        docs = []
        for payment in sorted(payment_by_counterparty.get(href, []), key=lambda item: item.get("moment") or ""):
            status, action = classify_payment(payment, supply_cache)
            docs.append(
                {
                    "payment_name": payment.get("name"),
                    "moment": payment.get("moment"),
                    "sum_rub": rub(payment.get("sum")),
                    "status": status,
                    "description": (payment.get("description") or "").replace("\n", " "),
                    "suggested_action": action,
                }
            )
        output.append(
            {
                "counterparty": counterparty.get("name"),
                "balance_rub": rub(row.get("balance")),
                "active_paymentouts": len(docs),
                "docs": docs,
            }
        )

    print(
        json.dumps(
            {
                "negative_counterparties": len(output),
                "counterparties": output,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
