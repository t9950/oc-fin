---
name: syle-ledger-hygiene
description: Use when cleaning and classifying Syle money records: missing counterparties, wrong direction, empty dates, unknown P&L meaning, broken links, founder or personal contamination, and historical payment repair.
---

# Syle Ledger Hygiene

Start by reading:

- `../../NOTION_ERP_SCHEMA_V1.md`
- `../../MANAGEMENT_ACCOUNTING_ARCHITECTURE.md`

Use this skill when the task is to make the ledger trustworthy again.

## Priority order

Repair money records in this order:

1. direction of money: incoming / outgoing / transfer / refund
2. amount and date presence
3. account and counterparty
4. accrual date
5. economic meaning in P&L
6. link to sale, receipt, or obligation
7. payment distribution if the link is one-to-many or partial

## What to fix

Focus on:

- `Платежи` without type
- `Платежи` without accrual date
- `Платежи` without counterparty
- records with missing required fields
- payments that should be tied to `Продажи`, `Приемки`, or `Обязательства`
- founder or personal money mixed into business flow

## Hard rules

- Do not hide ambiguity; mark it.
- Do not repair link structure with free text if a relation exists.
- Do not count a payment as business expense twice.
- When business and personal money are mixed, separate the fact first and only then classify.

## Output discipline

When reporting results, always state:

- what was fixed
- what remains ambiguous
- which records are still untrusted
- what the next smallest cleanup batch should be
