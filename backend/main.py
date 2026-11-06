"""Campus Customs backend for the React dashboard.

Start it from the backend/ folder:
    uvicorn main:app --reload --port 8000

Shop data comes through the MCP server. Agents can only prepare requests.
The approve route is the only place a person's click turns into a payment,
and every decision goes to the audit trail.
"""

import asyncio
import json
import os
import shutil
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import Client

import audit
import config
from models import HumanDecision, RunRequest
from team import run_ticket

run_lock = asyncio.Lock()
active_ticket: Optional[int] = None

CONTINUE_TASK = (
    "Ticket {ticket_id} is back from a person. Read the ticket and the board. If a "
    "payment or draft the ticket needs was never prepared, have the right agent "
    "prepare it. Do any work that is now unblocked, and resolve the ticket if nothing "
    "is left to do."
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Keep one connection to the MCP server open while the backend runs."""
    async with Client(config.MCP_SERVER_PATH) as client:
        app.state.mcp = client
        yield


app = FastAPI(title="Campus Customs Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def call_tool(request: Request, name: str, **arguments) -> dict:
    """Call one MCP tool. The backend has no other way to reach shop data."""
    result = await request.app.state.mcp.call_tool(name, arguments)
    return result.data


def require_ok(result: dict) -> dict:
    """Turn a refusal from an MCP tool into an error the dashboard can show."""
    if result.get("refused"):
        raise HTTPException(status_code=409, detail=result["reason"])
    return result


def record_human_action(event: str, ticket_id: int, **fields) -> None:
    audit.record(
        run_id=f"human-{uuid.uuid4().hex[:8]}",
        ticket_id=ticket_id,
        agent="human",
        depth=0,
        step=1,
        event=event,
        model=None,
        **fields,
    )


async def find_board_item(request: Request, item_id: int) -> dict:
    board = await call_tool(request, "list_board_items")
    for item in board["items"]:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail=f"No board item with ID {item_id}.")


@app.get("/tickets")
async def get_tickets(request: Request) -> dict:
    """Return the tickets, whether each one is resolved, and which one is running."""
    tickets = await call_tool(request, "list_tickets")
    return {**tickets, "running_ticket": active_ticket}


@app.post("/tickets/{ticket_id}/run")
async def run_ticket_route(
    ticket_id: int,
    request: Request,
    body: Optional[RunRequest] = None,
) -> dict:
    """Start the agent team on a ticket, or send it back after a person has acted."""
    global active_ticket
    ticket = await call_tool(request, "get_ticket", ticket_id=ticket_id)
    if not ticket["found"]:
        raise HTTPException(status_code=404, detail=ticket["message"])
    if ticket["status"] == "resolved":
        raise HTTPException(status_code=409, detail=f"Ticket {ticket_id} is already resolved.")
    if run_lock.locked():
        raise HTTPException(status_code=409, detail="Another ticket is running. Try again soon.")

    pending = await call_tool(
        request, "list_board_items", ticket_id=ticket_id, status="pending"
    )
    if pending["items"]:
        raise HTTPException(
            status_code=409,
            detail=f"Ticket {ticket_id} has requests waiting for a person to decide.",
        )

    task = None
    if ticket["status"] != "open":
        task = CONTINUE_TASK.format(ticket_id=ticket_id)

    note = body.note.strip() if body and body.note else ""
    if note:
        task = f"{task or f'Work ticket {ticket_id}.'} A person gave this instruction: {note}"
        record_human_action("human_decision", ticket_id, text=f"Note to the team: {note}")

    async with run_lock:
        active_ticket = ticket_id
        try:
            outcome = await run_ticket(ticket_id, task=task)
        except Exception as error:
            raise HTTPException(
                status_code=502,
                detail=f"The agent run failed: {type(error).__name__}. See the audit trail.",
            ) from error
        finally:
            active_ticket = None
    return outcome.model_dump()


@app.get("/events")
def get_events(
    limit: int = Query(default=50, ge=1, le=2000),
    ticket_id: Optional[int] = None,
) -> dict:
    """Return recent agent events, oldest first: what agents said and which tools they used."""
    if not config.AUDIT_PATH.exists():
        return {"events": []}
    trail = json.loads(config.AUDIT_PATH.read_text(encoding="utf-8"))
    if ticket_id is not None:
        trail = [entry for entry in trail if entry["ticket_id"] == ticket_id]
    return {"events": trail[-limit:]}


@app.get("/board")
async def get_board(request: Request, status: Optional[str] = None) -> dict:
    """Return requests and drafts on the board so the dashboard can refresh."""
    if status is None:
        return await call_tool(request, "list_board_items")
    return await call_tool(request, "list_board_items", status=status)


@app.post("/board/{item_id}/approve")
async def approve_item(item_id: int, decision: HumanDecision, request: Request) -> dict:
    """Carry out a person's approval. This is the only route that moves cash."""
    item = await find_board_item(request, item_id)
    if item["kind"] == "discount_request":
        tool = "decide_request"
        arguments = {
            "item_id": item_id,
            "decision": "approved",
            "decided_by": decision.decided_by,
        }
    else:
        tool = "pay"
        arguments = {"item_id": item_id, "approved_by": decision.decided_by}

    result = await call_tool(request, tool, **arguments)
    record_human_action(
        "human_decision",
        item["ticket_id"],
        tool=tool,
        args=arguments,
        result=json.dumps(result),
    )
    return require_ok(result)


@app.post("/board/{item_id}/reject")
async def reject_item(item_id: int, decision: HumanDecision, request: Request) -> dict:
    """Carry out a person's rejection. No money moves."""
    item = await find_board_item(request, item_id)
    arguments = {
        "item_id": item_id,
        "decision": "rejected",
        "decided_by": decision.decided_by,
    }
    result = await call_tool(request, "decide_request", **arguments)
    record_human_action(
        "human_decision",
        item["ticket_id"],
        tool="decide_request",
        args=arguments,
        result=json.dumps(result),
    )
    return require_ok(result)


@app.get("/cash")
async def get_cash(request: Request) -> dict:
    """Return the current checking balance from cash_accounts."""
    return await call_tool(request, "get_cash_balance", account="checking")


@app.post("/reset")
async def reset_database() -> dict:
    """Restore the working database from the original. The audit trail is kept."""
    if run_lock.locked():
        raise HTTPException(status_code=409, detail="Wait for the running ticket to finish.")

    temporary = config.WORKING_DB_PATH.with_suffix(".tmp")
    shutil.copyfile(config.ORIGINAL_DB_PATH, temporary)
    os.replace(temporary, config.WORKING_DB_PATH)
    record_human_action("database_reset", 0, text="Working database restored from the original.")
    return {"ok": True, "message": "The working database is back to its original values."}
