---
name: syle-procure-to-pay
description: Use when recording or repairing the supplier and procurement cycle in Syle: receipts, raw material intake, supplier obligations, outgoing payments, payment allocations, and historical reconstruction of purchases.
---

# Syle Procure To Pay

Start by reading `../../NOTION_ERP_SCHEMA_V1.md`.

Use this skill for supplier-side and raw-material-side events.

## Objects in scope

- `Приемки`
- `Приходы сырья`
- `Обязательства`
- `Платежи`
- `Распределения платежей`
- `Поставщики`
- `Склады`

## Workflow

1. Verify supplier and warehouse.
2. If the user reports an outgoing supplier payment and does not explicitly say the goods or service were not yet received, treat the fact as received by default.
3. Create `Приемка` for the factual or managerially reconstructed intake event.
4. If raw material quantities or lots are known, create or fix `Приходы сырья` and link them to `Приемка`.
5. Create `Обязательство` separately from the payment:
   - counterparty
   - amount
   - due date if known
   - account if relevant
   - status
6. Record or repair the money event in `Платежи`:
   - outgoing
   - accrual date filled
   - counterparty filled
   - if the payment only settles a separately recognized `Приемка` and/or `Обязательство`, set `Статья P&L = не влияет`
   - only keep P&L meaning on the payment itself when no receipt/obligation layer can be restored yet
7. Use `Распределения платежей` to connect the payment to `Приемка` and/or `Обязательство`.
   For supplier-side payments this is the default, not an exception, even for 1:1 links.
8. Update obligation status after distribution.

If exact SKU detail is still unavailable but the payment must stop creating a false negative supplier balance, create a short internal closing `Приемка`/supplier document the same day and mark in the comment that the fact is accepted as received by default unless noted otherwise later.

## Historical recovery

- If quantity, lot, or SKU detail is missing, do not invent it.
- In that case, keep `Приемка` as a managerial document with a comment about what could not be restored.
- Separate true procurement from founder funding, transfers, and personal spending.

## Comment rule

- For `Приемка` and linked supplier-side documents, write comments only in Russian.
- Keep the text short and factual: what was received, from whom, and why the document exists if it is a reconstruction.
- Do not leave English boilerplate, migration filler, or generic technical notes in the description.

## Completion check

Before finishing, confirm:

- supplier is explicit
- receipt exists
- obligation exists when money and accrual are separated in time
- payment is typed and dated
- distribution is explicit
