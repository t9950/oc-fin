---
name: syle-formula-to-tech-card
description: Use when Syle needs to mirror canonical recipe or premix facts from Google Sheets into a minimal operational tech card in Notion for packaging, batch trace, deterministic consumption, and cost flow without turning Notion into the source of recipe truth.
---

# Syle Formula To Tech Card

Start by reading:

- `../../NOTION_ERP_SCHEMA_V1.md`
- `../../MANAGEMENT_ACCOUNTING_ARCHITECTURE.md`
- `../syle-formula-change-control/SKILL.md`

Then check the live source-of-truth pointers on the main `Syle` page.

Current expected external sources:

- `Рецептура v0.6 (Sheets)`
- `Премикс v0.11 (Sheets)`

Use `gog` first for Google Sheets access.

## Purpose

This skill exists for the missing bridge:

- canonical formula in Sheets
- minimal operational tech card in Notion

The tech card in this phase is not a second canonical recipe.

It is an operating mirror for:

- packaging additions
- batch trace
- deterministic consumption inputs
- cost and stock flow

## Core model

Keep these layers separate:

- canonical recipe in Sheets != operational tech card in Notion
- premix recipe != finished-product recipe
- formula version != stock movement
- packing rules != recipe body

Current Syle rule:

- Sheets remains the canonical source for formula, premix, version, norms, and prices
- Notion stores only the minimum mirror needed to run operations reliably

`Натуральный` in Sheets maps to `без ароматизатора` / `БА` in the operating contour.

## What belongs in the operational tech card

Mirror only facts that operations need deterministically:

- product / taste identity
- linked canonical formula version
- linked premix version, if applicable
- ingredient list or norm references needed for stock logic
- target batch mass or other operating scale anchor
- packaging components that are not part of the canonical recipe body
- yield or conversion assumption, if explicitly known
- release status for operations
- comment about any unsynced gap

If the full formula body is not required for the operating task, do not duplicate it.

## Workflow

1. Confirm the canonical source.
   - Recipe and premix truth stays in Sheets.
2. Identify what must be mirrored into Notion.
   - which product or taste
   - which version
   - whether premix is involved
   - whether packaging additions are needed
3. Build or update the minimum operational tech card.
   - keep only fields needed for deterministic stock, packing, and cost flow
   - keep packaging explicit, not hidden in comments
4. Preserve historical meaning.
   - if an older batch used an older operational card or prior formula, do not silently overwrite that truth
5. Mark downstream readiness.
   - whether the card is ready for batch consumption
   - whether reorder or availability logic can already rely on it
   - what still remains only in Sheets
6. If deterministic sync is incomplete, mark the sync gap instead of letting AI fill it from memory.

## Hard rules

- Do not promote Notion to canonical recipe truth.
- Do not rewrite historical batch logic just because the current formula changed.
- Do not invent norms, yields, or packaging quantities.
- Do not hide packaging inside free text if the current schema can store it explicitly.
- Do not copy the whole Sheet into Notion unless the operating layer truly needs it.
- Do not claim deterministic batch consumption is ready if the required norms are still unsynced.

## Completion check

Before finishing, confirm:

- canonical version still lives in Sheets
- operational tech card contains only the minimum required mirror
- packaging additions are explicit
- historical batches are not silently reinterpreted
- any remaining sync gap is named directly
