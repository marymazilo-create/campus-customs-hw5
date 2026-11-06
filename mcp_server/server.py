"""Campus Customs MCP server.

The one place agents and people reach shop data. Tools read and update
data/campus_customs_new.db, and they only return what is in the database.
If a record does not exist, a tool says so instead of guessing.

Tools fall into three groups:
  - Read tools look up shop facts.
  - Prepare tools put requests and drafts on the board for review.
  - Human tools (pay, decide_request) are never given to an agent.
"""

import json
import sqlite3
from calendar import monthrange
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Iterator, Literal, Optional

from fastmcp import FastMCP

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_customs_new.db"

AGENT_NAMES = {"boss", "inventory", "accounting", "facilities", "customer_service"}
TICKET_STATUSES = {"open", "in_progress", "waiting_on_human", "resolved"}
MONEY_KINDS = ("payment_request", "purchase_order")

BOARD_TABLE = """
CREATE TABLE IF NOT EXISTS board_items (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    ticket_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    amount REAL,
    details TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_on TEXT NOT NULL,
    decided_by TEXT,
    decided_on TEXT,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
)
"""

mcp = FastMCP("campus-customs")


def _ensure_board() -> None:
    """Add the board table to the working copy. The original file is never touched."""
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute(BOARD_TABLE)
        connection.commit()
    finally:
        connection.close()


@contextmanager
def _read() -> Iterator[sqlite3.Connection]:
    """Open the working database in read-only mode."""
    _ensure_board()
    connection = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


@contextmanager
def _write() -> Iterator[sqlite3.Connection]:
    """Open one all-or-nothing transaction, so a failed step changes nothing."""
    _ensure_board()
    connection = sqlite3.connect(DB_PATH, isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("BEGIN IMMEDIATE")
        yield connection
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()


def _refuse(reason: str) -> dict:
    return {"ok": False, "refused": True, "reason": reason}


def _today(db: sqlite3.Connection) -> str:
    return db.execute("SELECT date_today FROM desk").fetchone()["date_today"]


def _add_month(day: str) -> str:
    """Move a YYYY-MM-DD date forward one calendar month."""
    current = date.fromisoformat(day)
    year = current.year + (current.month == 12)
    month = current.month % 12 + 1
    last_day = monthrange(year, month)[1]
    return date(year, month, min(current.day, last_day)).isoformat()


def _item(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["details"] = json.loads(item["details"])
    return item


def _add_board_item(
    db: sqlite3.Connection,
    kind: str,
    ticket_id: int,
    status: str,
    amount: Optional[float],
    details: dict,
    created_by: str,
) -> dict:
    cursor = db.execute(
        "INSERT INTO board_items "
        "(kind, ticket_id, status, amount, details, created_by, created_on) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (kind, ticket_id, status, amount, json.dumps(details), created_by, _today(db)),
    )
    row = db.execute(
        "SELECT * FROM board_items WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return _item(row)


def _ticket_exists(db: sqlite3.Connection, ticket_id: int) -> bool:
    row = db.execute("SELECT id FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return row is not None


def _open_invoices(db: sqlite3.Connection, vendor_id: int) -> list[dict]:
    rows = db.execute(
        "SELECT id, amount, due_date, status, description FROM invoices "
        "WHERE vendor_id = ? AND status = 'open' ORDER BY due_date",
        (vendor_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _cash_view(db: sqlite3.Connection, row: sqlite3.Row) -> dict:
    """Show an account with every pending money request already subtracted."""
    items = db.execute(
        "SELECT id, kind, ticket_id, amount, details FROM board_items "
        "WHERE status = 'pending' AND kind IN (?, ?) ORDER BY id",
        MONEY_KINDS,
    ).fetchall()
    pending = sum(item["amount"] for item in items)
    return {
        **dict(row),
        "pending_requests": [
            {
                "item_id": item["id"],
                "kind": item["kind"],
                "ticket_id": item["ticket_id"],
                "amount": item["amount"],
                "payee": json.loads(item["details"])["payee"],
            }
            for item in items
        ],
        "pending_requests_total": pending,
        "balance_after_pending": round(row["balance"] - pending, 2),
        "note": (
            "balance_after_pending already subtracts every pending request listed "
            "here. Do not subtract them again."
        ),
    }


# ---------------------------------------------------------------- read tools


@mcp.tool
def get_shop_date() -> dict:
    """Get today's date for the shop from desk.date_today.

    Use this date, never the real calendar date, to decide what is overdue.
    """
    with _read() as db:
        row = db.execute("SELECT date_today, notes FROM desk").fetchone()
    return dict(row)


@mcp.tool
def list_tickets() -> dict:
    """List every ticket with its status, including resolved tickets."""
    with _read() as db:
        rows = db.execute(
            "SELECT id, type, requester, subject, status, created_at FROM tickets "
            "ORDER BY id"
        ).fetchall()
    tickets = [{**dict(row), "resolved": row["status"] == "resolved"} for row in rows]
    return {"tickets": tickets}


@mcp.tool
def list_open_tickets() -> dict:
    """List every ticket that is not resolved, oldest first."""
    with _read() as db:
        rows = db.execute(
            "SELECT id, type, requester, subject, status, created_at FROM tickets "
            "WHERE status != 'resolved' ORDER BY created_at"
        ).fetchall()
    return {"tickets": [dict(row) for row in rows]}


@mcp.tool
def get_ticket(ticket_id: int) -> dict:
    """Get one ticket, including the SKU, size, lease, or invoice it links to."""
    with _read() as db:
        row = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        return {"found": False, "message": f"No ticket record for ticket ID {ticket_id}."}
    return {"found": True, **dict(row)}


@mcp.tool
def get_ticket_briefing(ticket_id: int) -> dict:
    """Get what you need to start on a ticket in one call.

    Returns the ticket, the shop date, checking cash after pending requests,
    and this ticket's board items. Use it once instead of separate lookups.
    """
    with _read() as db:
        ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if ticket is None:
            return {"found": False, "message": f"No ticket record for ticket ID {ticket_id}."}
        account = db.execute(
            "SELECT * FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()
        items = db.execute(
            "SELECT * FROM board_items WHERE ticket_id = ? ORDER BY id", (ticket_id,)
        ).fetchall()
        return {
            "found": True,
            "shop_date": _today(db),
            "ticket": dict(ticket),
            "cash": _cash_view(db, account),
            "board_items": [_item(item) for item in items],
        }


@mcp.tool
def check_stock(sku: str, size: str) -> dict:
    """Check how many units of one SKU and size are on hand.

    Use this to compare stock with the quantity a ticket requests.
    Sizes are values such as S, M, L, XL, or OS for one-size items.
    """
    with _read() as db:
        row = db.execute(
            "SELECT sku, name, size, qty, location FROM inventory "
            "WHERE sku = ? AND size = ?",
            (sku, size),
        ).fetchone()

    if row is None:
        return {
            "found": False,
            "message": f"No inventory record for SKU {sku} in size {size}.",
        }
    return {"found": True, **dict(row)}


@mcp.tool
def list_vendors() -> dict:
    """List vendors with their specialty and lead time in days.

    No table links a SKU to a vendor, so choose by specialty.
    """
    with _read() as db:
        rows = db.execute(
            "SELECT id, name, specialty, lead_days FROM vendors ORDER BY id"
        ).fetchall()
    return {"vendors": [dict(row) for row in rows]}


@mcp.tool
def get_invoice(invoice_id: int) -> dict:
    """Get one invoice, its vendor, and how many days overdue it is by shop date."""
    with _read() as db:
        row = db.execute(
            "SELECT invoices.*, vendors.name AS vendor_name FROM invoices "
            "JOIN vendors ON vendors.id = invoices.vendor_id WHERE invoices.id = ?",
            (invoice_id,),
        ).fetchone()
        if row is None:
            return {
                "found": False,
                "message": f"No invoice record for invoice ID {invoice_id}.",
            }
        today = _today(db)

    days_late = (date.fromisoformat(today) - date.fromisoformat(row["due_date"])).days
    return {
        "found": True,
        **dict(row),
        "shop_date": today,
        "days_overdue": max(days_late, 0) if row["status"] == "open" else 0,
    }


@mcp.tool
def get_open_invoices(vendor_id: int) -> dict:
    """List a vendor's open invoices.

    Use this before ordering from a vendor. A vendor will not ship new
    product while it has an open unpaid invoice.
    """
    with _read() as db:
        vendor = db.execute(
            "SELECT id, name FROM vendors WHERE id = ?",
            (vendor_id,),
        ).fetchone()
        if vendor is None:
            return {
                "found": False,
                "message": f"No vendor record for vendor ID {vendor_id}.",
            }
        open_invoices = _open_invoices(db, vendor_id)

    return {
        "found": True,
        "vendor_id": vendor["id"],
        "vendor_name": vendor["name"],
        "open_invoices": open_invoices,
        "total_open": sum(invoice["amount"] for invoice in open_invoices),
        "can_ship_new_product": not open_invoices,
    }


@mcp.tool
def get_pricing(sku: str) -> dict:
    """Get a SKU's unit cost, list price, and margin."""
    with _read() as db:
        row = db.execute("SELECT * FROM pricing WHERE sku = ?", (sku,)).fetchone()
    if row is None:
        return {"found": False, "message": f"No pricing record for SKU {sku}."}

    margin = row["list_price"] - row["unit_cost"]
    return {
        "found": True,
        **dict(row),
        "margin_per_unit": round(margin, 2),
        "margin_pct": round(margin / row["list_price"] * 100, 1),
    }


@mcp.tool
def get_cash_balance(account: str = "checking") -> dict:
    """Get an account's balance and what is left after pending requests."""
    with _read() as db:
        row = db.execute(
            "SELECT * FROM cash_accounts WHERE name = ?", (account,)
        ).fetchone()
        if row is None:
            return {"found": False, "message": f"No cash account named {account}."}
        return {"found": True, **_cash_view(db, row)}


@mcp.tool
def get_lease(lease_id: int) -> dict:
    """Get one lease's space, landlord, monthly rent, and next due date.

    Use this to confirm a rent notice against the shop's own lease record.
    """
    with _read() as db:
        row = db.execute(
            "SELECT id, space_name, landlord, monthly_rent, next_due, notes "
            "FROM leases WHERE id = ?",
            (lease_id,),
        ).fetchone()

    if row is None:
        return {
            "found": False,
            "message": f"No lease record for lease ID {lease_id}.",
        }
    return {"found": True, **dict(row)}


@mcp.tool
def list_board_items(
    ticket_id: Optional[int] = None,
    status: Optional[str] = None,
) -> dict:
    """List requests and drafts on the board, optionally by ticket or status."""
    query = "SELECT * FROM board_items WHERE 1 = 1"
    values: list = []
    if ticket_id is not None:
        query += " AND ticket_id = ?"
        values.append(ticket_id)
    if status is not None:
        query += " AND status = ?"
        values.append(status)

    with _read() as db:
        rows = db.execute(query + " ORDER BY id", values).fetchall()
    return {"items": [_item(row) for row in rows]}


# ------------------------------------------------------------- prepare tools


@mcp.tool
def prepare_payment(
    ticket_id: int,
    kind: Literal["invoice", "rent"],
    ref_id: int,
    prepared_by: str,
) -> dict:
    """Put a payment request on the board for human approval.

    This does not move money. The amount and payee come from the invoice
    or lease record, so they cannot be typed in. ref_id is the invoice ID
    or lease ID.
    """
    if prepared_by not in AGENT_NAMES:
        return _refuse(f"{prepared_by} is not a shop agent.")

    with _write() as db:
        if not _ticket_exists(db, ticket_id):
            return _refuse(f"No ticket record for ticket ID {ticket_id}.")

        if kind == "invoice":
            row = db.execute(
                "SELECT invoices.*, vendors.name AS vendor_name FROM invoices "
                "JOIN vendors ON vendors.id = invoices.vendor_id "
                "WHERE invoices.id = ?",
                (ref_id,),
            ).fetchone()
            if row is None:
                return _refuse(f"No invoice record for invoice ID {ref_id}.")
            if row["status"] != "open":
                return _refuse(f"Invoice {ref_id} is {row['status']}, not open.")
            amount = row["amount"]
            details = {
                "payment_kind": "invoice",
                "ref_id": ref_id,
                "payee": row["vendor_name"],
                "due_date": row["due_date"],
                "description": row["description"],
            }
        else:
            row = db.execute("SELECT * FROM leases WHERE id = ?", (ref_id,)).fetchone()
            if row is None:
                return _refuse(f"No lease record for lease ID {ref_id}.")
            amount = row["monthly_rent"]
            details = {
                "payment_kind": "rent",
                "ref_id": ref_id,
                "payee": row["landlord"],
                "due_date": row["next_due"],
                "description": f"Rent for {row['space_name']}",
            }

        duplicates = db.execute(
            "SELECT id, details FROM board_items "
            "WHERE kind = 'payment_request' AND status = 'pending'"
        ).fetchall()
        for existing in duplicates:
            other = json.loads(existing["details"])
            if other["payment_kind"] == kind and other["ref_id"] == ref_id:
                return _refuse(f"Board item {existing['id']} already requests this payment.")

        item = _add_board_item(
            db, "payment_request", ticket_id, "pending", amount, details, prepared_by
        )
    return {"ok": True, "awaiting_human_approval": True, "item": item}


@mcp.tool
def prepare_purchase_order(
    ticket_id: int,
    vendor_id: int,
    sku: str,
    size: str,
    qty: int,
    prepared_by: str,
) -> dict:
    """Put a purchase order on the board for human approval.

    Purchase orders are paid up front once a human approves them. The cost
    is qty times the unit cost in pricing. The order is flagged as blocked
    if the vendor still has an open unpaid invoice.
    """
    if prepared_by not in AGENT_NAMES:
        return _refuse(f"{prepared_by} is not a shop agent.")
    if qty <= 0:
        return _refuse("Quantity must be more than zero.")

    with _write() as db:
        if not _ticket_exists(db, ticket_id):
            return _refuse(f"No ticket record for ticket ID {ticket_id}.")

        vendor = db.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,)).fetchone()
        if vendor is None:
            return _refuse(f"No vendor record for vendor ID {vendor_id}.")

        stock = db.execute(
            "SELECT name FROM inventory WHERE sku = ? AND size = ?", (sku, size)
        ).fetchone()
        if stock is None:
            return _refuse(f"No inventory record for SKU {sku} in size {size}.")

        price = db.execute("SELECT unit_cost FROM pricing WHERE sku = ?", (sku,)).fetchone()
        if price is None:
            return _refuse(f"No pricing record for SKU {sku}.")

        blockers = [invoice["id"] for invoice in _open_invoices(db, vendor_id)]
        arrival = date.fromisoformat(_today(db)) + timedelta(days=vendor["lead_days"])
        details = {
            "vendor_id": vendor_id,
            "payee": vendor["name"],
            "sku": sku,
            "name": stock["name"],
            "size": size,
            "qty": qty,
            "unit_cost": price["unit_cost"],
            "lead_days": vendor["lead_days"],
            "expected_arrival": arrival.isoformat(),
            "blocked_by_open_invoices": blockers,
        }
        amount = round(qty * price["unit_cost"], 2)
        item = _add_board_item(
            db, "purchase_order", ticket_id, "pending", amount, details, prepared_by
        )
    return {"ok": True, "awaiting_human_approval": True, "item": item}


@mcp.tool
def prepare_discount_request(
    ticket_id: int,
    sku: str,
    qty: int,
    discount_pct: float,
    reason: str,
    prepared_by: str,
) -> dict:
    """Put a discount request on the board for human sign-off.

    Every discount needs a human unless a human has set up a sale. The
    database has no sale records, so all discounts go through this tool.
    """
    if prepared_by not in AGENT_NAMES:
        return _refuse(f"{prepared_by} is not a shop agent.")
    if qty <= 0:
        return _refuse("Quantity must be more than zero.")
    if not 0 < discount_pct <= 100:
        return _refuse("Discount must be more than 0% and no more than 100%.")

    with _write() as db:
        if not _ticket_exists(db, ticket_id):
            return _refuse(f"No ticket record for ticket ID {ticket_id}.")

        price = db.execute("SELECT * FROM pricing WHERE sku = ?", (sku,)).fetchone()
        if price is None:
            return _refuse(f"No pricing record for SKU {sku}.")

        discounted = round(price["list_price"] * (1 - discount_pct / 100), 2)
        details = {
            "sku": sku,
            "qty": qty,
            "discount_pct": discount_pct,
            "list_price": price["list_price"],
            "discounted_price": discounted,
            "unit_cost": price["unit_cost"],
            "margin_per_unit_after": round(discounted - price["unit_cost"], 2),
            "below_cost": discounted < price["unit_cost"],
            "reason": reason,
        }
        item = _add_board_item(
            db, "discount_request", ticket_id, "pending", None, details, prepared_by
        )
    return {"ok": True, "awaiting_human_approval": True, "item": item}


@mcp.tool
def save_customer_draft(ticket_id: int, message: str, prepared_by: str) -> dict:
    """Save a customer message on the board as a draft.

    Drafts are never sent. A person decides what happens to them.
    """
    if prepared_by not in AGENT_NAMES:
        return _refuse(f"{prepared_by} is not a shop agent.")
    if not message.strip():
        return _refuse("The draft message is empty.")

    with _write() as db:
        ticket = db.execute(
            "SELECT requester FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
        if ticket is None:
            return _refuse(f"No ticket record for ticket ID {ticket_id}.")

        details = {"to": ticket["requester"], "message": message.strip()}
        item = _add_board_item(
            db, "customer_draft", ticket_id, "draft", None, details, prepared_by
        )
    return {"ok": True, "sent": False, "item": item}


@mcp.tool
def update_ticket(ticket_id: int, status: str, note: str, updated_by: str) -> dict:
    """Update a ticket's status and add a dated note.

    Status must be open, in_progress, waiting_on_human, or resolved. A
    ticket cannot be resolved while a request for it is still pending.
    """
    if updated_by not in AGENT_NAMES:
        return _refuse(f"{updated_by} is not a shop agent.")
    if status not in TICKET_STATUSES:
        return _refuse(f"Status must be one of: {', '.join(sorted(TICKET_STATUSES))}.")

    with _write() as db:
        ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if ticket is None:
            return _refuse(f"No ticket record for ticket ID {ticket_id}.")

        if status == "resolved":
            pending = db.execute(
                "SELECT COUNT(*) AS total FROM board_items "
                "WHERE ticket_id = ? AND status = 'pending'",
                (ticket_id,),
            ).fetchone()
            if pending["total"]:
                return _refuse(f"Ticket {ticket_id} still has pending requests.")

        entry = f"[{_today(db)}, {updated_by}] {note.strip()}"
        notes = f"{ticket['notes']}\n{entry}" if ticket["notes"] else entry
        db.execute(
            "UPDATE tickets SET status = ?, notes = ? WHERE id = ?",
            (status, notes, ticket_id),
        )
    return {"ok": True, "ticket_id": ticket_id, "status": status, "notes": notes}


# --------------------------------------------------------------- human tools


@mcp.tool
def pay(item_id: int, approved_by: str, account: str = "checking") -> dict:
    """Pay a pending request after a human approves it. Human use only.

    No agent has this tool. It refuses if cash would go negative, if the
    request is not pending, or if a vendor still has an open unpaid invoice.
    When it pays, it updates payments, cash_accounts, board_items, and the
    invoice or lease.
    """
    approver = approved_by.strip()
    if not approver or approver.lower() in AGENT_NAMES:
        return _refuse("A named human must approve every payment.")

    with _write() as db:
        row = db.execute("SELECT * FROM board_items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            return _refuse(f"No board item with ID {item_id}.")
        if row["kind"] not in MONEY_KINDS:
            return _refuse(f"Board item {item_id} is not a payment request or purchase order.")
        if row["status"] != "pending":
            return _refuse(f"Board item {item_id} is {row['status']}, not pending.")

        details = json.loads(row["details"])
        amount = row["amount"]

        if row["kind"] == "purchase_order":
            blockers = _open_invoices(db, details["vendor_id"])
            if blockers:
                numbers = ", ".join(str(invoice["id"]) for invoice in blockers)
                return _refuse(f"{details['payee']} still has open invoice(s): {numbers}.")

        today = _today(db)
        withdrawn = db.execute(
            "UPDATE cash_accounts SET balance = ROUND(balance - ?, 2), date = ? "
            "WHERE name = ? AND balance >= ?",
            (amount, today, account, amount),
        )
        if withdrawn.rowcount != 1:
            balance = db.execute(
                "SELECT balance FROM cash_accounts WHERE name = ?", (account,)
            ).fetchone()
            if balance is None:
                return _refuse(f"No cash account named {account}.")
            return _refuse(
                f"Not enough cash: {account} has ${balance['balance']:,.2f} "
                f"and this payment is ${amount:,.2f}."
            )

        if row["kind"] == "purchase_order":
            payment_kind, ref_id = "purchase_order", item_id
        else:
            payment_kind, ref_id = details["payment_kind"], details["ref_id"]

        if payment_kind == "invoice":
            db.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (ref_id,))
        elif payment_kind == "rent":
            lease = db.execute(
                "SELECT next_due FROM leases WHERE id = ?", (ref_id,)
            ).fetchone()
            db.execute(
                "UPDATE leases SET next_due = ? WHERE id = ?",
                (_add_month(lease["next_due"]), ref_id),
            )

        payment = db.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (payment_kind, ref_id, amount, account, today, approver),
        )
        db.execute(
            "UPDATE board_items SET status = 'paid', decided_by = ?, decided_on = ? "
            "WHERE id = ?",
            (approver, today, item_id),
        )
        balance = db.execute(
            "SELECT balance FROM cash_accounts WHERE name = ?", (account,)
        ).fetchone()["balance"]

    return {
        "ok": True,
        "payment_id": payment.lastrowid,
        "kind": payment_kind,
        "amount": amount,
        "approved_by": approver,
        "balance_after": balance,
    }


@mcp.tool
def decide_request(
    item_id: int,
    decision: Literal["approved", "rejected"],
    decided_by: str,
) -> dict:
    """Approve a discount, or reject any pending request. Human use only.

    No agent has this tool. Payments and purchase orders are approved by
    calling pay, so money only moves in one place.
    """
    decider = decided_by.strip()
    if not decider or decider.lower() in AGENT_NAMES:
        return _refuse("A named human must make this decision.")

    with _write() as db:
        row = db.execute("SELECT * FROM board_items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            return _refuse(f"No board item with ID {item_id}.")
        if row["status"] != "pending":
            return _refuse(f"Board item {item_id} is {row['status']}, not pending.")
        if decision == "approved" and row["kind"] != "discount_request":
            return _refuse("Use pay to approve a payment request or purchase order.")

        db.execute(
            "UPDATE board_items SET status = ?, decided_by = ?, decided_on = ? WHERE id = ?",
            (decision, decider, _today(db), item_id),
        )
    return {"ok": True, "item_id": item_id, "status": decision, "decided_by": decider}


if __name__ == "__main__":
    mcp.run(show_banner=False)
