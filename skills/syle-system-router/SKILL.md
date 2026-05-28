---
name: syle-system-router
description: Use when the user asks how to work in the Syle Notion system, when the operational contour is unclear, or when a real business event needs to be restored into the correct chain of order, shipment, payment, receipt, obligation, and allocation.
---

# Syle System Router

Use this skill as the entrypoint for the live Syle Notion system.

Start by reading:

- `../../NOTION_ERP_SCHEMA_V1.md`
- `../../MANAGEMENT_ACCOUNTING_ARCHITECTURE.md`

Read `../../memory/syle_business_decisions.md` only if pricing, trial packs, or revenue meaning affects the operation.

## Core model

Do not collapse the system back into one flat payments table.

Keep these separations:

- order != shipment
- payment != товарный документ
- procurement != receipt lines
- obligation != cash movement
- warehouse event != finance classification

## Routing

Pick one contour before editing anything:

- sales and client cash -> `syle-order-to-cash`
- supplier purchase and raw material intake -> `syle-procure-to-pay`
- broken, empty, or ambiguous money records -> `syle-ledger-hygiene`
- weekly review, close, or integrity check -> `syle-control-close`

## Default workflow

1. Identify the real fact that happened.
2. Check which object is missing: order, shipment, receipt, obligation, payment, or allocation.
3. Create the minimum chain needed to reflect the fact.
4. Link documents and money through relations, not comments alone.
5. Mark any unrecoverable gap explicitly.

## Hard rules

- Never invent quantities, lots, or dates that are not recoverable from facts.
- If historical recovery is partial, create a managerial document with a comment and state the limitation.
- Keep founder or personal money separate from business operations.
- If one payment touches several documents, use `Распределения платежей`.
