# Harness Notes: Campus Customs Multi-Agent Operations

This is a working file. We will add to it as the assignment goes on.

## Database files

| File | Purpose |
|---|---|
| `data/campus_customs.db` | Original database. Never edit it. Use it to reset. |
| `data/campus_customs_new.db` | Working copy. The MCP server and backend read and update this file. |

**To reset before a full run:** copy `campus_customs.db` over `campus_customs_new.db`.

## Tables

The starting state below comes from the original database. "Today" for the shop is 2026-08-31.

### desk (1 row)
**Fields:** `date_today`, `notes`

**Why it matters for agents:** It sets "today" for the shop, so every agent uses this date, not the real one, to decide what is overdue.

### tickets (3 rows, all open)
**Fields:** `id`, `type`, `requester`, `subject`, `sku`, `size`, `qty`, `lease_id`, `invoice_id`, `status`, `notes`, `created_at`

**Why it matters for agents:** This is the work queue. Boss reads each ticket here, and its fields point agents to the right stock, lease or invoice.

### inventory (10 rows)
**Fields:** `sku`, `name`, `size`, `qty`, `location`

**Why it matters for agents:** Inventory uses it to check stock by SKU and size and to spot shortfalls. Each SKU and size pair has one row.

### pricing (4 rows)
**Fields:** `sku`, `unit_cost`, `list_price`

**Why it matters for agents:** Accounting uses it to work out margins, discounts and restock costs.

### vendors (3 rows)
**Fields:** `id`, `name`, `specialty`, `lead_days`

**Why it matters for agents:** Inventory uses it to choose who can restock an item and how long that will take.

### leases (1 row)
**Fields:** `id`, `space_name`, `landlord`, `monthly_rent`, `next_due`, `notes`

**Why it matters for agents:** Facilities uses it to confirm the rent amount, the due date and who gets paid.

### cash_accounts (1 row)
**Fields:** `name`, `balance`, `date`

**Why it matters for agents:** This is the shop's available cash. The pay tool checks it and must refuse any payment that would make it negative.

### invoices (1 row)
**Fields:** `id`, `vendor_id`, `amount`, `due_date`, `status`, `description`

**Why it matters for agents:** It shows what the shop owes. A vendor with an open unpaid invoice will not ship new product.

### payments (0 rows)
**Fields:** `id`, `kind`, `ref_id`, `amount`, `account`, `paid_at`, `approved_by`

**Why it matters for agents:** This is the record of money paid out. Each row shows what was paid and which human approved it.

### board_items (added by the MCP server)
**Fields:** `id`, `kind`, `ticket_id`, `status`, `amount`, `details`, `created_by`, `created_on`, `decided_by`, `decided_on`

**Why it matters for agents:** This is the board where payment requests, purchase orders, discount requests and customer drafts wait for a person. The server adds it to the working copy only, so `campus_customs.db` never changes, and it comes back automatically after a reset.

## How the tables connect

**Declared links in the database:**
- `tickets.lease_id` → `leases.id`
- `tickets.invoice_id` → `invoices.id`
- `invoices.vendor_id` → `vendors.id`

**Links with no declared key, which agents must follow by matching values:**
- `tickets.sku` + `tickets.size` → `inventory.sku` + `inventory.size`
- `tickets.sku` → `pricing.sku`
- `inventory.sku` → `pricing.sku`
- `payments.ref_id` → an invoice or lease, depending on `payments.kind`
- `payments.account` → `cash_accounts.name`

**No table links a SKU to a vendor.** The only guide is `vendors.specialty`.

## The three open tickets

### Ticket 101: customer order
- **Request:** Tauhid Zaman wants 1 `CC-TEE-WHITE` tee in size S.
- **Stock:** Size S has 0 on hand, so the order is short 1 unit.
- **Linked invoice:** Invoice 501 is $840.00 to Bulldog Print Co (vendor 1) for "Rush reprint CC-TEE-WHITE S." It was due 2026-08-28, is still open, and is 3 days overdue.
- **Blocker:** Bulldog Print Co will not ship new product until invoice 501 is paid.
- **Timing:** Bulldog Print Co has a 5-day lead time, so a restock ordered on 2026-08-31 arrives about 2026-09-05.
- **Agents involved:** Inventory, Accounting, Customer Service, Boss

### Ticket 102: rent notice
- **Request:** Elm City Properties says rent is due in 2 days.
- **Linked lease:** Lease 1, Chapel Street shop, is $2,400.00 a month, due 2026-09-02. It is not overdue yet.
- **Blocker:** None, but payment needs human approval.
- **Name check:** The landlord is Elm City Properties. Elm City Gifts is a separate company and is a vendor.
- **Agents involved:** Facilities, Accounting, Boss

### Ticket 103: price override
- **Request:** Yale AI Club wants 20 `CC-HOOD-NAVY` hoodies in size M and is asking for a bulk discount. It gives no discount amount.
- **Stock:** Size M has 8 on hand, so the order is short 12 units.
- **Pricing:** The hoodie costs $22.00 and lists at $58.00, a margin of $36.00 per unit, or about 62%.
- **Blocker:** The ticket does not link to an invoice, but Bulldog Print Co is the likely supplier because its specialty is apparel reprint. If so, invoice 501 blocks this restock too.
- **Agents involved:** Inventory, Accounting, Customer Service, Boss

## Cash across all three tickets

| Item | Amount | Cash left |
|---|---:|---:|
| Starting cash | | $3,400.00 |
| Invoice 501 | $840.00 | $2,560.00 |
| Rent for lease 1 | $2,400.00 | $160.00 |
| 1 tee at $8.00 cost | $8.00 | $152.00 |
| 12 hoodies at $22.00 cost | $264.00 | **-$112.00** |

**The shop cannot pay for everything if restocks are paid up front.** All four items total $3,512.00, which is $112.00 more than the $3,400.00 available. The agents need to look at the tickets together, not one at a time, because no revenue comes in to close the gap.

After the invoice, rent and tee, $152.00 is left. That covers 6 hoodies at $22.00.

## First three MCP tools

The server is in `mcp_server/server.py` and connects to `data/campus_customs_new.db`. All three tools are read-only.

### `check_stock(sku, size)`
- **Table it reads:** `inventory`
- **Ticket it unlocks:** Ticket 103 (it also helps with ticket 101)
- **Why it is the right tool:** Ticket 103 asks for 20 `CC-HOOD-NAVY` hoodies in size M, and checking that exact SKU and size shows only 8 on hand, which tells the agents the order is 12 short and needs a restock before anyone quotes or promises 20.

### `get_open_invoices(vendor_id)`
- **Tables it reads:** `invoices` and `vendors`
- **Ticket it unlocks:** Ticket 101 (it also helps with ticket 103)
- **Why it is the right tool:** Ticket 101 needs a size S tee that is out of stock, and looking up vendor 1 shows open invoice 501 for $840.00, the blocker that must be paid before Bulldog Print Co will ship a restock.

### `get_lease(lease_id)`
- **Table it reads:** `leases`
- **Ticket it unlocks:** Ticket 102
- **Why it is the right tool:** Ticket 102's notice says only that rent is due in 2 days, so lease 1 supplies the facts Accounting needs to prepare the payment: $2,400.00 to Elm City Properties, due 2026-09-02.

## Connecting the MCP server

**Two different AIs use this server:**
- **Claude Code** is the vibe coder that helps build the project. It connects through `.mcp.json` so we can test the tools.
- **`gpt-6-luna`** will be the model behind the shop's agents, reached through Portkey in later problems. It does not build anything and is not part of this connection.

**Connection file:** `.mcp.json` at the project root names the server `campus-customs` and starts `mcp_server/server.py` with `uv`.

**Test evidence:** `output/mcp_smoke.json` records the prompt, tool name and tool output for each tool. All three outputs matched a separate query of `data/campus_customs_new.db`.

**Lesson from the test:** Claude Code's written answers used the real calendar date, not the shop date of 2026-08-31. The tools don't return "today" yet, so the agents need a way to read `desk.date_today`.

## Shop decisions

- **Board:** Requests and drafts go in `board_items`.
- **Purchase orders:** They are paid up front once a human approves them.
- **Discounts:** Every discount needs human sign-off unless a human has set up a sale. The database has no sale records, so today every discount goes to a person.
- **Payment order when cash is short:** Rent, then the overdue invoice, then the tee, then the hoodies.

## Agent team

All five agents use `gpt-6-luna` through Portkey with reasoning effort set to `none`, because the model refuses tool calls on this connection otherwise. Their code is in `backend/team.py`, and each has its own prompt in `backend/prompts/`. Every agent also has the `delegate` tool, so any agent can hand work to any other agent. `delegate` is not an MCP tool because it connects agents and does not touch shop data.

| Agent | Job | MCP tools |
|---|---|---|
| Boss | Reads each ticket, decides who works on it, makes final calls | `get_ticket_briefing`, `list_open_tickets`, `list_board_items`, `update_ticket` |
| Inventory | Checks stock, spots shortfalls, finds which vendor can restock | `get_ticket_briefing`, `check_stock`, `list_vendors`, `get_invoice`, `get_open_invoices`, `get_pricing` |
| Accounting | Watches cash and invoices, checks margins, prepares requests for approval | `get_ticket_briefing`, `list_vendors`, `get_invoice`, `get_open_invoices`, `get_pricing`, `get_cash_balance`, `get_lease`, `list_board_items`, `prepare_payment`, `prepare_purchase_order`, `prepare_discount_request` |
| Facilities | Handles leases and rent notices | `get_ticket_briefing`, `get_lease` |
| Customer Service | Drafts customer messages | `get_ticket_briefing`, `check_stock`, `list_board_items`, `save_customer_draft` |

## All MCP tools

The server has 20 tools. All shop facts come through these tools from `data/campus_customs_new.db`.

| Tool | Table it uses | Used by | What it does |
|---|---|---|---|
| `get_ticket_briefing` | `tickets`, `desk`, `cash_accounts`, `board_items` | All agents | Reads the ticket, shop date, cash and this ticket's board items in one call |
| `get_shop_date` | `desk` | None | Reads the shop's "today"; the briefing replaced it for agents |
| `list_tickets` | `tickets` | Backend | Lists every ticket and whether it is resolved |
| `list_open_tickets` | `tickets` | Boss | Lists tickets that are not resolved |
| `get_ticket` | `tickets` | Backend | Reads one ticket and its links |
| `check_stock` | `inventory` | Inventory, Customer Service | Reads stock for one SKU and size |
| `list_vendors` | `vendors` | Inventory, Accounting | Reads vendor specialties and lead times |
| `get_invoice` | `invoices`, `vendors`, `desk` | Inventory, Accounting | Reads one invoice, its vendor and days overdue |
| `get_open_invoices` | `invoices`, `vendors` | Inventory, Accounting | Shows whether a vendor can ship |
| `get_pricing` | `pricing` | Inventory, Accounting | Reads cost, list price and margin |
| `get_cash_balance` | `cash_accounts`, `board_items` | Accounting | Reads cash and what is left after pending requests |
| `get_lease` | `leases` | Accounting, Facilities | Reads rent, landlord and due date |
| `list_board_items` | `board_items` | Boss, Accounting, Customer Service | Reads requests and drafts |
| `prepare_payment` | Reads `invoices`, `vendors`, `leases`; writes `board_items` | Accounting | Requests a payment and takes the amount from the record |
| `prepare_purchase_order` | Reads `vendors`, `inventory`, `pricing`, `invoices`; writes `board_items` | Accounting | Requests a restock and flags any invoice blocking it |
| `prepare_discount_request` | Reads `pricing`; writes `board_items` | Accounting | Requests human sign-off on a discount |
| `save_customer_draft` | Reads `tickets`; writes `board_items` | Customer Service | Saves a message that is never sent |
| `update_ticket` | Writes `tickets`; reads `board_items` | Boss | Changes status and adds a dated note |
| `pay` | Writes `payments`, `cash_accounts`, `board_items`, `invoices`, `leases` | **Humans only** | Pays a pending request |
| `decide_request` | Writes `board_items` | **Humans only** | Approves a discount or rejects a request |

## Backend routes

The backend is in `backend/main.py`. From the `backend/` folder, start it with `uvicorn main:app --reload --port 8000`. It runs at `http://localhost:8000` and reaches shop data through the MCP server.

- `GET /tickets`: Returns the three tickets and whether each is open or resolved.
- `POST /tickets/{ticket_id}/run`: Runs the agent team on one ticket, or sends it back after a person has acted, with an optional note for Boss. It refuses while a request is waiting for a person.
- `GET /events`: Returns recent audit events, showing what each agent said and which tools it used. It can be filtered by `limit` and `ticket_id`.
- `GET /board`: Returns the requests and drafts on the board so the dashboard can refresh.
- `POST /board/{item_id}/approve`: Carries out a person's approval. This is the only route that moves cash, and it needs the person's name in `decided_by`.
- `POST /board/{item_id}/reject`: Records a person's rejection, and no money moves.
- `GET /cash`: Returns the current checking balance from `cash_accounts`.
- `POST /reset`: Restores `campus_customs_new.db` from the original and keeps the audit trail.

## Dashboard

The React desk is in `frontend/` and calls these routes at `http://localhost:8000`. The backend allows the Vite page at `http://localhost:5173`. Start the backend, then run `npm run dev` from `frontend/`. Design choices are in `output/design.md`.

When a ticket goes back to the team, a person can add a "Note to the team." The note goes to Boss as an instruction and is recorded in the audit trail. This was added after the agents agreed the tee order fit the budget but would not prepare it without authorization.

## Audit trail

Every run appends to `output/audit_trail.json` and never wipes it. Each entry records the time, run ID, ticket, agent, who delegated to it, delegation depth, step number, event and model. Depending on the event, it also records the tool, arguments, result, model text and token counts.

Events are `run_start`, `model_response`, `tool_call`, `tool_result`, `delegation`, `delegation_refused`, `run_end`, `run_error`, `human_decision` and `database_reset`. Human entries show `human` as the agent and have no model. If the audit file is damaged, the run stops so that no action goes unrecorded.

## Final run results

The final run started from a reset database with $3,400.00 in checking. All three tickets finished as `resolved`, using only `gpt-6-luna`.

| Ticket | Runs | Model calls | Tokens | Cash change | Why |
|---|---:|---:|---:|---:|---|
| 101 | 5 | 93 | 243,159 | -$848.00 | Invoice 501 ($840.00) and the tee order ($8.00) |
| 102 | 2 | 23 | 49,607 | -$2,400.00 | Rent for lease 1 |
| 103 | 2 | 42 | 112,109 | $0.00 | Discount approved, and no restock ordered |
| **Total** | **9** | **158** | **404,875** | **-$3,248.00** | Ending balance: **$152.00** |

The ending balance matches `cash_accounts`. Mary approved all three payments and the discount.

**What the run showed:**
- **Token limits:** Tighter limits and the briefing tool did not reduce total use. First-pass tokens rose from about 169,000 to about 207,000, and only Ticket 103 went down. Most of the waste came from agents repeating work, not from lookups.
- **Human instructions:** Ticket 101 needed notes from Mary to prepare the tee order and to define when the ticket was finished. Without them, the agents kept treating the order as unauthorized and the delivery as unfinished.
- **Tool checks mattered:** The `get_cash_balance` note fixed a repeated double-counting error that a prompt line alone did not fix. Duplicate payment requests were refused by the tools.

Evidence is in `output/desk_tickets.html`, `output/resolved_tickets.json`, `output/resolved_board.html` and `output/audit_trail.json`.

## Safety guardrails

These protect real customers and real money.

**Built into the tools:**
- **Humans control payments:** No agent has `pay` or `decide_request`. Code removes them from every agent's tool list.
- **Amounts come from records:** Agents cannot type a payment amount.
- **Cash cannot go negative:** `pay` refuses a payment larger than the balance.
- **No double payments:** A paid item cannot be paid again, and a pending payment cannot be requested twice.
- **Vendor rule:** `pay` refuses a purchase order while that vendor has an open invoice.
- **All or nothing:** A payment updates every table or none of them.
- **Messages stay drafts:** The system has no tool that sends anything.
- **Tickets stay honest:** A ticket cannot be resolved while a request for it is pending.
- **Least access:** Each agent gets only the tools its job needs. The one exception is the briefing, which shows every agent the cash position, read-only, to save model calls.
- **Full record:** Every step goes to the audit trail.

**A real company would also want:**
- Named logins for approvers, so `approved_by` can't simply be typed in
- Two approvers above a set dollar amount
- A person reviewing every message before a customer sees it
- Customer data kept out of model prompts unless it is needed
- An audit log stored where it can't be edited
- Regular reviews of agent mistakes, and a switch that stops all agents at once

## Token limits

These are set in `backend/config.py`. Delegated work counts toward the same ticket totals.

| Limit | Setting | Why |
|---|---|---|
| Model calls per agent run | 14 | Stops one agent from looping |
| Model calls per ticket | 40 | Caps total work on a ticket |
| Tokens per ticket | 120,000 | Caps cost directly |
| Delegations per ticket | 4 | Stops the team from passing work around |
| Delegation depth | 2 | Stops long chains of handoffs |

An agent also cannot delegate to itself, to an agent already waiting on it, or give another agent the same task twice. If a delegated agent reaches its limit, control returns to the agent that asked, so Boss can still finish the ticket or ask a person.

The first real run of Ticket 101 stopped at the earlier limits of 10 calls per agent, 30 calls per ticket and 60,000 tokens per ticket, so the limits were raised. A later run reached 40 calls because agents kept passing work back and forth, so handoffs back up the chain are now refused. Ticket 103 later used about 111,000 tokens, so delegation limits were tightened from 8 to 4 per ticket and from depth 3 to depth 2. Agents now start with one briefing call and trust the facts in a hand-off. `gpt-6-luna` is set in code, and `MODEL_NAME` in `.env` is ignored.
