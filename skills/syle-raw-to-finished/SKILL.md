---
name: syle-raw-to-finished
description: Use when recording or repairing the production-side conversion in Syle: a batch release, managerial movement from raw materials to finished goods, or any event where raw inputs become saleable product and must be reflected without inventing unsupported lot detail.
---

# Syle Raw To Finished

Start by reading:

- `../../NOTION_ERP_SCHEMA_V1.md`
- `../../MANAGEMENT_ACCOUNTING_ARCHITECTURE.md`

Use this skill for the production event itself, not for procurement or sales around it.

## Objects in scope

- `Склады`
- `Приходы сырья`
- `Списания`
- `Оприходования`
- `Инвентаризации`

If the event also involves supplier payment or client shipment, route that part to another skill:

- supplier side -> `syle-procure-to-pay`
- client side -> `syle-order-to-cash`

## Current model boundary

The workspace does not yet define a full batch-costing or production-order layer.

Because of that:

- do not invent a hidden BOM
- do not fake lot precision that was not recorded
- do not pretend stock balances are exact if the movement was reconstructed later

Use the existing warehouse and adjustment objects as a managerial trace of the event.

## Workflow

1. Identify the factual production event:
   - what was produced
   - when
   - from which raw inputs, if known
   - into which warehouse
2. Check whether the raw-material side is already present in `Приходы сырья`.
3. If raw consumption is known, reflect it through `Списания` or explicit managerial note linked to the production event.
4. Reflect the finished-goods side through `Оприходования` into the correct warehouse.
5. If the event is reconstructed after the fact, attach a comment that states which quantities or component links are reliable and which are not.
6. If an inventory correction is the cleanest truthful representation, use `Инвентаризации` plus linked `Оприходования` rather than fabricating a cleaner story.

## Hard rules

- One production event should produce one clear managerial trace.
- Separate true production output from freebies, samples, damage, and personal withdrawals.
- If sample packs or promo units were created, mark them as a separate meaning from saleable stock.
- If a finished batch is uncertain, preserve the uncertainty instead of overfitting the record.

## Completion check

Before finishing, confirm:

- the warehouse is explicit
- the finished-goods appearance is recorded
- the raw-material reduction is either linked or explicitly marked as unresolved
- any reconstruction limits are written down
