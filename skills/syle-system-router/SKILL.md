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
- recipe version, premix change, or canonical formula control in Sheets -> `syle-formula-change-control`
- canonical recipe or premix in Sheets that needs an operational tech card mirror in Notion -> `syle-formula-to-tech-card`
- production conversion and batch release -> `syle-raw-to-finished`
- unpacked vs packed finished stock, packaging consumption, reorder, or availability logic -> `syle-bulk-pack-and-availability`
- minimum stock, reorder control, or deterministic availability review -> `syle-reorder-and-availability-control`
- stock count, opening balances, surplus, shortage, or stock correction -> `syle-inventory-reconciliation`
- broken, empty, or ambiguous money records -> `syle-ledger-hygiene`
- weekly review, close, or integrity check -> `syle-control-close`

## Skill gap rule

If the user asks for a typical Notion operation and no existing Syle skill fits cleanly:

1. Name the gap explicitly.
2. Distinguish one-off work from recurring workflow.
3. If recurring, propose creating a shared skill before this turns into repeated ad hoc handling.
4. After a short user approval, add the new skill, update `AGENTS.md`, and extend this router if needed.

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
