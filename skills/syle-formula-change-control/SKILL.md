---
name: syle-formula-change-control
description: Use when Syle needs controlled work around recipe or premix changes, version truth in Google Sheets, and the managerial release of a new formula into the Notion operating system without silently rewriting history or inventing a full tech-card layer.
---

# Syle Formula Change Control

Start by reading:

- `../../NOTION_ERP_SCHEMA_V1.md`
- `../../MANAGEMENT_ACCOUNTING_ARCHITECTURE.md`

Then check the live source-of-truth pointers on the main `Syle` page.

Current expected external sources:

- `Рецептура v0.6 (Sheets)`
- `Премикс v0.11 (Sheets)`

If the canonical version is already explicit in Sheets, treat that as sufficient version truth.

Do not create a fake “more official” version in Notion just because operations live there.

Use `gog` first for Google Sheets access.

## Purpose

This skill is for formula governance, not for ad hoc recipe guessing.

It exists to answer:

- what formula is currently canonical
- what changed
- which products or ingredients were affected
- whether the change is only experimental or already released into operations
- which production events should use which formula version

## Core model

Keep these layers separate:

- canonical formula in Sheets != operating data in Notion
- formula change != production event
- formula version != stock movement
- future intended formula != released working formula

In the current Syle phase, the expected split is:

- recipe and premix truth stay in Sheets
- Notion stores the minimum operating mirror needed for stock, packaging, batch trace, and cost flow
- packaging additions or operational packing rules may be mirrored in Notion even if the full recipe body stays outside

Do not force the full recipe body into Notion earlier than needed.

If Sheets is still the safer canonical source, keep it there and only move the minimum operational facts into Notion.

## What this skill should control

- formula version identity
- date of change
- scope of change
- whether premix also changed
- affected ingredients
- affected products / tastes
- release status:
  - draft
  - test only
  - released for production
- note about which downstream contours now need updates:
  - tech card
  - batch issue
  - себестоимость
  - reorder assumptions

## Workflow

1. Confirm the source of truth first.
   - If the formula is still canonical in Sheets, treat Notion as an operating mirror only.
2. Identify the change event.
   - what changed
   - why
   - which version becomes current
   - whether this is formula, premix, or both
3. Record the minimum managerial trace in Notion.
   - version label
   - effective date
   - affected products
   - affected ingredients
   - operational status
   - comment on what must be re-synced downstream
   - whether Notion needs only packaging or other operating additions rather than a full recipe copy
4. Do not rewrite old production or historical stock just because a new formula became current.
5. If an existing batch, cost, or availability logic depends on the prior formula, keep the old operational truth explicit.
6. If the change should propagate into deterministic calculations later, mark the sync requirement rather than letting AI “remember it”.

## Hard rules

- Do not edit historical stock or batch facts just because Sheets changed today.
- Do not let one “current formula” silently overwrite the version used by older batches.
- Do not copy the whole recipe into Notion unless the operating contour truly needs it.
- Do not duplicate a canonical version in Notion if Sheets already carries the authoritative version truth cleanly.
- Do not use AI as the source of formula truth when the canonical fact lives in Sheets.
- If a version or release state is unclear, mark it explicitly instead of guessing.

## Completion check

Before finishing, confirm:

- canonical source is explicit
- changed version is explicit
- impacted products or tastes are explicit
- downstream sync requirements are explicit
- historical batches are not silently reinterpreted
