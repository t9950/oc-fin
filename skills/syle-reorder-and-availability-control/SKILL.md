---
name: syle-reorder-and-availability-control
description: Use when Syle needs formulas-first control over minimum stock, reorder flags, availability for production or orders, and deterministic exception logic where AI only reviews what formulas and scripts surface.
---

# Syle Reorder And Availability Control

Start by reading:

- `../../NOTION_ERP_SCHEMA_V1.md`
- `../../MANAGEMENT_ACCOUNTING_ARCHITECTURE.md`

Then read the currently relevant operating skills if needed:

- `../syle-bulk-pack-and-availability/SKILL.md`
- `../syle-formula-change-control/SKILL.md`

## Purpose

This skill defines how Syle should answer, deterministically where possible:

- what is below minimum stock
- what must be reordered
- whether a planned batch can be produced
- whether a requested packed SKU can be fulfilled
- whether the bottleneck is raw material, unpacked finished stock, or packaging

## Formulas-first policy

Default implementation order:

1. Notion relations, rollups, and formulas
2. deterministic script or automation, only if formulas are not enough
3. AI review only for exceptions, ambiguity, or human-facing summaries

If a number can be computed without AI, it should be computed without AI.

AI should not be the primary engine for:

- stock truth
- reorder quantity
- availability math
- bottleneck detection

## Core objects

- `Сырьё`
- `Продукция`
- `Фасовки`
- `Партии выпуска`
- `Расход сырья`
- `Списания`
- `Оприходования`
- `Склады`

## Minimum deterministic outputs

For raw materials:

- current stock
- minimum stock
- below-minimum flag
- reorder suggestion

For finished goods:

- packed stock on hand
- unpacked finished stock on hand
- whether packing stock is sufficient for the requested SKU

For production planning:

- enough / not enough for a planned batch
- which component blocks the batch first

## Recommended logic

### Raw materials

Use the `Сырьё` database as the control hub.

Expected deterministic fields:

- current stock from incoming lots minus raw consumption
- `Мин. остаток, г`
- reorder flag like `current <= minimum`
- optional reorder amount if a target replenishment rule exists

Do not wait for AI to tell you that a formula already knows stock is low.

### Finished goods

Keep separate:

- packed finished stock
- unpacked finished stock
- packaging stock

Availability for a packed SKU should be able to answer:

- available immediately from packed stock
- available after repacking from unpacked stock
- blocked by missing packaging

### Production / batch availability

If recipe norms are already canonical in Sheets and mirrored into the operating layer, calculate:

- how much batch mass is feasible
- whether premix or any raw ingredient is the bottleneck
- whether the planned batch exceeds current stock

If deterministic norms are not yet synced, do not invent availability with AI. Mark the sync gap explicitly.

## Scripts and automation

Use deterministic automation only where formulas become impractical, for example:

- generating many consumption lines from one planned batch
- syncing tech-card values from Sheets into the operating layer
- bulk-updating availability helper fields

Any script should be:

- input-driven
- reproducible
- auditable

## AI role

AI is allowed to:

- review weekly exceptions
- summarize what dropped below minimum
- flag suspicious contradictions
- ask short fact-check questions
- prioritize cleanup

AI is not allowed to become the hidden calculator when formulas or scripts can do the job reliably.

## Hard rules

- Do not let historical backfill override the post-inventory baseline.
- Do not mix raw-material reorder logic with finished-goods packing logic.
- Do not merge packaging shortage into raw-material shortage.
- Do not compute “availability” from guesses when deterministic inputs are missing.
- If a formula cannot yet be trusted because the source fields are incomplete, state that directly.

## Completion check

Before finishing, confirm:

- formulas or rollups drive the main status flags
- any script use is deterministic and explicit
- AI is only reviewing surfaced exceptions
- baseline cutoffs are preserved
- packed, unpacked, and packaging layers are not collapsed together
