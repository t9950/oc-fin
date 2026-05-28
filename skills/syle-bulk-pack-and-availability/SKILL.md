---
name: syle-bulk-pack-and-availability
description: Use when Syle needs to track finished goods in both packed and unpacked form, keep packaging stock separate from product stock, and implement reorder or availability logic through formulas or deterministic automations before involving AI.
---

# Syle Bulk Pack And Availability

Start by reading:

- `../../NOTION_ERP_SCHEMA_V1.md`
- `../../MANAGEMENT_ACCOUNTING_ARCHITECTURE.md`

Use this skill for stock logic, availability checks, repacking flow, and reorder control.

## Objects in scope

- `Продукция`
- `Фасовки`
- `Партии выпуска`
- `Списания`
- `Оприходования`
- `Склады`
- `Сырьё`

If the task also changes formula norms or recipe structure, route that part to the recipe/tech-card contour instead of inventing hidden consumption rules here.

## Core model

Keep these layers separate:

- raw materials != finished goods
- packed finished goods != unpacked finished goods
- product stock != packaging stock
- deterministic calculation != AI interpretation

Unpacked finished product is still finished goods.

It is not:

- raw material
- packaging
- a vague note outside stock logic

It exists so the system can answer:

- what is already saleable in packed form
- what can be quickly packed from bulk finished stock
- whether packaging is the bottleneck rather than formula or raw material

## Formulas-first policy

Default order of implementation:

1. Notion formulas, rollups, and relations
2. deterministic script or automation, if formulas are not enough
3. AI review only for exceptions, ambiguity, and control

Examples of what should be deterministic:

- current stock
- below-minimum flag
- reorder amount
- availability against a planned batch or order
- packaging bottleneck detection

Examples of what may need script support:

- generating many stock-consumption rows from one packing or batch event
- syncing deterministic tech-card inputs from Sheets into Notion

Examples of what AI may do:

- weekly exception review
- detect suspicious gaps
- ask short fact-check questions
- summarize what needs attention

AI should not be the primary calculator for stock truth.

## Workflow

1. Identify which stock layer the fact belongs to:
   - raw material
   - unpacked finished product
   - packed finished product
   - packaging / container / lid
2. For production output, record the finished-goods appearance first:
   - what product was produced
   - when
   - how much was packed immediately
   - how much was left unpacked
3. Keep unpacked finished stock explicit through `Партии выпуска` fields and linked managerial trace.
4. When repacking from unpacked finished stock into a SKU:
   - reduce unpacked finished quantity
   - increase packed finished quantity
   - consume packaging at the moment of actual packing, not earlier
5. For packaging logic, keep packaging stock separate from finished-product stock even if the current model stores it through temporary managerial conventions.
6. Use formulas for:
   - below-minimum checks
   - reorder flags
   - maximum producible quantity where norms are already known
   - “enough / not enough” checks for a planned order or packing run
7. If the current schema cannot represent a needed deterministic link cleanly, name the schema gap explicitly instead of hiding it in free text.

## Hard rules

- Do not mix unpacked finished product with raw materials.
- Do not treat unused containers or lids as finished-product stock.
- Do not consume packaging before the actual packing event.
- Do not let AI invent quantities, norms, or availability math that can be derived deterministically.
- If a formula or rollup can express the logic reliably, prefer that over prompts.
- If a script is introduced, keep its inputs explicit and auditable.

## Completion check

Before finishing, confirm:

- packed and unpacked finished stock are separated
- packaging is not merged into product stock
- deterministic calculation path is explicit
- any remaining AI role is limited to review and exceptions
- any schema gap is named directly
