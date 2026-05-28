---
name: syle-order-to-cash
description: Use when recording or repairing the client sales cycle in Syle: orders, shipments, incoming payments, payment allocations, sales status changes, and historical recovery of closed or partially closed sales.
---

# Syle Order To Cash

Start by reading `../../NOTION_ERP_SCHEMA_V1.md`.

Use this skill for any client-side revenue chain.

## Objects in scope

- `Продажи`
- `Отгрузки`
- `Платежи`
- `Распределения платежей`
- `Клиенты`
- `Склады`

## Workflow

1. Verify that the client order exists in `Продажи`.
2. Fill or fix the minimum sales fields: client, planned shipment date, and order status.
3. Create an `Отгрузка` only for the factual shipment event.
4. Link `Отгрузка` to the order, client, and warehouse.
5. Record or repair the money event in `Платежи`:
   - incoming
   - accrual date filled
   - counterparty filled
   - `Статья P&L = выручка` when it is client revenue
6. If one payment covers one document only, still make sure the relation is explicit.
7. If one payment covers several documents or only part of one document, create `Распределения платежей`.
8. Change order status only from facts:
   - shipped if the shipment is real
   - closed if shipment and payment side are materially completed

## Historical recovery

- Recover the factual chain first, cosmetic cleanup second.
- If shipment lines are missing, do not fake them.
- If payment exists but shipment evidence is partial, create the shipment with a clear comment about the limitation.

## Completion check

Before finishing, confirm:

- order <-> shipment link exists
- payment is typed and dated
- counterparty is filled
- P&L meaning is filled
- allocation exists where needed
