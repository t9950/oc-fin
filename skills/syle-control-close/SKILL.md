---
name: syle-control-close
description: Use when running daily or weekly control over the Syle system, checking integrity between orders, shipments, receipts, obligations, and payments, or preparing a simple period close without redesigning the whole architecture.
---

# Syle Control Close

Start by reading:

- `../../NOTION_ERP_SCHEMA_V1.md`
- `../../MANAGEMENT_ACCOUNTING_ARCHITECTURE.md`

Use this skill for control, not for redesign.

## Review queues

Check these queues first:

- sales without shipments
- shipments without clear sales link
- incoming payments without revenue meaning
- outgoing payments without supplier or obligation link
- obligations without due date or status
- receipts without raw material lines where detail is expected
- records missing required fields
- known defective or empty payment records

## Closing order

1. Close the current month first.
2. Only then backfill historical gaps.
3. Use linked facts, not assumptions, for any summary.

## What good control looks like

- every meaningful money event has direction, date, counterparty, and accrual meaning
- every client revenue event is tied to a sale and shipment path
- every supplier settlement is tied to a receipt and/or obligation path
- unresolved gaps are visible in a short backlog, not hidden inside normal views

## Reporting rule

If data is still dirty, say so directly. Do not present the close as precise.

End with one operational next step only, for example:

- clean the remaining untyped payments
- close one supplier chain end-to-end
- repair the last sale without shipment
