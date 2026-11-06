# Campus Customs Multi-Agent Operations

MGT 409 Homework 5, Mary Hiratsuka Mazilo

A team of five AI agents runs the back office of a campus shop. Boss, Inventory, Accounting, Facilities, and Customer Service work open tickets through an MCP server, and a person watches them on a React desk and approves every payment.

All agents use `gpt-6-luna` through Portkey.

## Setup

You need Python 3.10 or later, Node.js, and a Portkey API key.

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your key to `.env`. Do not commit that file.

## Copy the original database for a clean run

`data/campus_customs.db` is the original and should never change. `data/campus_customs_new.db` is the working copy, and it holds the final state of my run: three resolved tickets and $152.00 in checking.

To start clean, copy the original over the working copy:

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

## Start the MCP server

The backend starts the MCP server automatically, so you do not need a separate step to run the app. To start it by itself, run this from the project root:

```bash
python mcp_server/server.py
```

It waits for an MCP client to connect, so it prints little on its own. `.mcp.json` connects it to Claude Code, which needs `uv` installed.

## Start the FastAPI backend

In a new terminal, from the project root:

```bash
source .venv/bin/activate
cd backend
uvicorn main:app --reload --port 8000
```

The backend runs at http://localhost:8000.

## Start the React board

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

The desk opens at http://localhost:5173.

## Reset the database before the full three-ticket run

Before running all three tickets, reset the working copy. With the desk open, click **Start the day over** in the passbook, then **Restore**. You can also run:

```bash
curl -X POST http://localhost:8000/reset
```

Either option restores $3,400.00 and clears the board. The audit trail is kept.

## Run the tickets

1. Pick a ticket on the corkboard and press **Start the team**.
2. Watch the agents in the notebook.
3. Enter your name in the in-tray, then approve or decline each request.
4. Press **Send back to the team**, and add a note if the agents need a decision.
5. Repeat until the ticket has a red Resolved stamp.

Agents only prepare requests. Only a person's approval moves money.

## Where to look

| File | What it shows |
|---|---|
| `AI_prompts.md` | My prompts for each problem |
| `output/desk_tickets.html` | Expected and Actual for each ticket, plus the Cash and Reflection tabs |
| `output/resolved_tickets.json` | Each ticket's outcome, agent work, and approvals |
| `output/resolved_board.html` | Screenshots of the resolved tickets on the board |
| `output/audit_trail.json` | Every agent step and human decision |
| `output/harness.md` | Tables, MCP tools, agents, routes, dashboard, and safety rules |
| `output/design.md` | Design choices for the desk |
| `output/mcp_smoke.json` | MCP tool test evidence |
| `output/github_url.txt` | This repository's URL |
