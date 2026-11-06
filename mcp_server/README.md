# Campus Customs MCP Server

## Purpose

An MCP server gives AI agents a shared set of tools for reaching outside systems. This server lets every Campus Customs agent look up shop records the same way, so their answers come from the database and not from guesses.

## Database

The server uses `data/campus_customs_new.db`, the working copy of the shop database. It does not use the original, `data/campus_customs.db`, which is kept for resets.

The server also adds a `board_items` table to the working copy for requests and drafts.

## Tools

The server has 20 tools. If a record does not exist, a tool says so instead of guessing.

**Read tools**

| Tool | What it returns |
|---|---|
| `get_ticket_briefing(ticket_id)` | The ticket, shop date, cash after pending requests, and this ticket's board items |
| `get_shop_date()` | The shop's "today" from `desk.date_today` |
| `list_tickets()` | Every ticket and whether it is resolved |
| `list_open_tickets()` | Tickets that are not resolved |
| `get_ticket(ticket_id)` | One ticket and its links |
| `check_stock(sku, size)` | The quantity on hand and location for one SKU and size |
| `list_vendors()` | Vendor specialties and lead times |
| `get_invoice(invoice_id)` | One invoice, its vendor, and days overdue |
| `get_open_invoices(vendor_id)` | A vendor's open invoices, their total, and whether the vendor can ship new product |
| `get_pricing(sku)` | Unit cost, list price, and margin |
| `get_cash_balance(account)` | The balance and what is left after pending requests |
| `get_lease(lease_id)` | A lease's space, landlord, monthly rent, and next due date |
| `list_board_items(ticket_id, status)` | Requests and drafts on the board |

**Prepare tools**

These put items on the board. None of them moves money or contacts anyone.

| Tool | What it does |
|---|---|
| `prepare_payment(ticket_id, kind, ref_id, prepared_by)` | Requests an invoice or rent payment for human approval |
| `prepare_purchase_order(ticket_id, vendor_id, sku, size, qty, prepared_by)` | Requests a restock, paid up front once a human approves |
| `prepare_discount_request(ticket_id, sku, qty, discount_pct, reason, prepared_by)` | Requests human sign-off on a discount |
| `save_customer_draft(ticket_id, message, prepared_by)` | Saves a customer message as a draft |
| `update_ticket(ticket_id, status, note, updated_by)` | Changes a ticket's status and adds a dated note |

**Human tools**

No agent can use these.

| Tool | What it does |
|---|---|
| `pay(item_id, approved_by, account)` | Pays a pending request and updates the database, or refuses if the rules aren't met |
| `decide_request(item_id, decision, decided_by)` | Approves a discount or rejects a pending request |

## Connection

`.mcp.json` at the project root connects this server to Claude Code. It starts the server with `uv`, so `uv` must be installed. Open Claude Code from the project root so the path to `mcp_server/server.py` works.
