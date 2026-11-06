# AI Prompts Log: Homework 5, Campus Customs Multi-Agent Operations

MGT 409, AI Foundations for Managers, Fall 2026
Mary Hiratsuka Mazilo

This file logs what I typed to my vibe coder, one section per problem. Prompts are recorded word for word.

---

## Problem 1: Vibe coder prompts

**My prompt:**

> Problem 1 vibe coder prompts
> per usual, we need a "AI_prompts.md" to update as we push through this assignment.
>
> I'll walk you throught each of the prompts problem by problem and will include:
>
> * problem number and title
> * please capture at least one prompt i use that i've typed in my own words
> * a follow-up prompt and the rational behind it

**Follow-up prompt:** None needed.

**What was lacking after the first prompt:** Nothing. The first prompt covered what the log needs.

---

## Problem 2: Study the Campus Customs database

**My prompt:**

> Problem 2 study the campus customs database
>
> We need to open "data/campus_customs.db" and review every table with relevant fields. Make a copy of the og file to "data/campus_customs_new.db" then in later problems update that working copy.
>
> We need to study the three open tickets to see how they link to other tables
>
> We can start "output/harness.md" for each table we need a list of the fields and one short line explaining why the table matters for agents
>
> let's keep developing this file as we will use it later in this assignment

**Follow-up prompt:** None needed so far.

**What was lacking after the first prompt:** Nothing so far.

---

## Problem 3: Build the MCP server

**My prompt:**

> Problem 3 build the mcp server
>
> New we need to create an MCP server in "mcp_server/" with FastMCP
>
> We want it to talk to "data/campus_customs_new.db" we will not need a connection or to run it in this problem
>
> Each agent in this assignment will use the tolls in this MCP server. Moving along we will add additional tools later, but for the time being what are three tools we will need for the tickets in the database?
>
> Can you help me by giving me some ideas with clear names? Please NEVER create data, only use the info in the database
>
> In "output/harness.md" i need you to list each of the three MCP tools we land on. And we also need to include:
>
> * which table it reads
> * which ticket it supports (101, 103, or 103)
> * include a sentence on why that tool is the best one for that ticket - keep in mind we need more info than vague reasoning, for example, "reads inventory" is a poor answer please help me do better when adding info regarding the tool used for the ticket
>
>
> Also, we need a short "mcp_server/README.md" file added that clarifies what the purpose of a MCP server is, which database files it uses and the three tools in it.

**Follow-up prompt:**

> yes, lets go with the three tools you reccommended, and yes confirming that the tickets should be 101, 102 and 103, thank you!

**What was lacking after the first prompt:** My first prompt asked for tool ideas, so I still needed to choose the final three, and I had mistyped the ticket numbers.

---

## Problem 4: Add the MCP server to the vibe coder and test each tool

**My prompt:**

> Problem 4 add the MCP server to vibe coder and test each tool
>
> now we need to add the MCP server to claude (or whatever vibe coder we're using - i get confused by the whole gpt-luna step). We just need to make sure you can use the tools we're building.
>
> Then we need to save the connection JSON text in "mcp.json" at the project root (or wherever makes sense).
>
> Once connected, lets test each of the three MCP tools we created. Then document the evidence in "Output/mcp_smoke.json" For every tool we need to document:
>
> * prompt i created for you
> * tool name
> * tool output (needs to match values in "data/campus_customs_new.db"

**Follow-up prompt:** None needed so far.

**What was lacking after the first prompt:** Nothing so far.

---

## Problem 5: Build the agent team and grow the MCP tools

**My prompt:**

> Problem 5 build the agent team and grow the MCP tools
>
> now we need to build agentic team for Campus Customs with PydanticAI: boss, inventory, accounting, facilities and customer service
>
> We need to include: prompts, models, and agent loops so they can work together, delegate, and maintain full connectivity.
>
> Then we put the agent prompts in "backend/prompts/" one file per agent.
>
> Include data types in "backend/models.py"  and the agent files under "backend/" layout isn't as important as long as the 5 roles are clear.
>
> We need the portkey_api_key and only "gpt-6-luna" for every agent. so i'll need your help as usual pulling the portkey
>
> I'll work to write each prompt with shop rules that are needed by the agent. I'll need your help to make the prompts more detailed to cover details of each agent's work/scope as I'll want to get more points here.
>
> What are some tools we can add for each agent? We'll need them in the MCP server to they can take care of open tickets.
>
> Additionally shop facts need to come from MCP server over "data/campus_cusstoms_new.db" - you are NOT to invent a second shop-tools layer that bypasses MCP
>
> The agents need to be connected so that they append to "output/audit_trail.json" when they run - be sure each agent-loop step, record enough to audit and review later.
>
> In "output/harness.md" list each agent and each MCP tool (including ones in this prompt) along with the table and tool it uses.
>
> Ad short safety sections, the guardrails a real company would want when agents connect with real customers and actual money, plus limits that make sure we aren't blowing through tokens.
>
> Update "mcp_server/readme.md" so the tool list matches what we have now.

**Follow-up prompt:**

> 1 - yes okay to add "board_itmes"
> Purchase orders - can be paid upfront, once a human approves
> Discount rule - always need human sign-off unless a sale has been implimented by a human
> I agree with the order.
>
> Yes, update the tools

**What was lacking after the first prompt:** My first prompt asked for tool ideas but did not settle where requests and drafts live, when purchase orders get paid, the discount rule, or which payments come first when cash is short.

**Second follow-up prompts:**

> what are some examples i could use for the rough bullets for Boss, Inventory, Accounting, Facilities and Customer Service are fine, in your own words. Prompts score the most on this problem. I'll expand them and show you before saving to

> Perfect lets go with those notes

**What was lacking after the first follow-up:** I still needed the bullets for each agent's prompt. Claude wrote example bullets, I approved them as they were, and Claude expanded them into the five files in `backend/prompts/`.

**Third follow-up prompt:**

> Boss
>
> * triage and route cleanly
> * gate keep and require human approval
> * solve deadlocks and resource conflicts
> * enforce dependencies before sign-off
>
> Inventory
>
> * Check physical variance and SKU matching
> * Apply vendor selection judgment
> * Block procurement on bad standing
> * Handoffs
>
> Accounting
>
> * Verify funds
> * Prioritize cash
> * Prep drafts
> * Report deficits
>
> Facilities
>
> * audit rent notices
> * varify details
>
> Customer Service
>
> * draft messages ONLY
> * share only actual facts and stock numbers
> * communicate delays clearly and manage expectations
>
> General rules
>
> * use current shop date as "today"
> * rely on tool data; state gaps; never make up data
> * stay in lane and delegate tasks outside scope to the appropriate agent

**What was lacking after the second follow-up:** I wanted to set out each agent's core job in my own words. The five prompts in `backend/prompts/` cover each of these points.

---

## Problem 6: Plan the three tickets

**My prompt:**

> Problem 6 plan the three tickets
>
> prior to wiring the backend, lets document what I expect the tame to do on each open ticket.
>
> Create "output/desk_tickets.html" a page I can double-click with a tab per ticket (101, 102, 103).
>
> Also include empty cash and reflection tabs to use later (leave blank for now)
>
> Each ticket tab, i need an expected section filled, leave space for an actual section to fill once we run the agents.
>
> each tickets expected section i will need to write in my own word:
>
> * who the boss needs to call first and why
> * all agent delegations I anticipate
> * which MCP tools to expect that run to use
>
>
> I need to make a guess as to what will happen then run the agents

**Follow-up prompts:**

> Ticket 101
>
> 1. Who does Boss call first, and why? Inventory to double check if there are any size small shirts available. The boss will also need to delegate the linked invoice 501 to Accounting
> 2. Which delegations do you expect? If no small shirts available, then inventory hand off to accounting to order more and accounting to hand off to customer service to communicate when the item will ship.
> 3. Which MCP tools do you expect the run to use? get_ticket, check_stock, prepare_purchase_order, save_customer_draft, get_invoice, prepare_payment

> Ticket 102
>
> 1. Who does Boss call first, and why? Boss would call facilities first because they check the rent notices against the lease
> 2. Which delegations do you expect? Boss -> Facilities -> Accounting
> 3. Which MCP tools do you expect the run to use? get_ticket, get_lease, get_invoice, get_open_invoices, prepare_payment"

> Ticket 103
>
> 1. Who does Boss call first, and why? Boss would call customer service because they confirm discounts
> 2. Which delegations do you expect? Boss -> Customer Service -> Inventory -> Accounting -> Customer Service
> 3. Which MCP tools do you expect the run to use? get_ticket, check_stock, prepare_discount_request, save_customer_draft

**What was lacking after the first prompt:** The first prompt set up the page, but my guesses for each ticket still had to be written in my own words. I revised them after Claude pointed out where tools and delegations were mixed up.

**Second follow-up prompt:**

> Please update

**What was lacking after the first follow-up:** My Ticket 103 guess said Customer Service confirms discounts, which is not how the shop works. Claude reworded that ticket's three answers: Boss calls Accounting first, the chain is Boss -> Accounting -> Inventory -> Customer Service, and `get_pricing` is added.

---

## Problem 7: Plan backend routes

**My prompt:**

> Problem 7 Plan backened routes
>
> In the next problem we will need a redact frontend dashboard, and it needs a backend it can call.
>
> In "backend/main.py" use FastAPI and create routes that can do:
>
> * Return the 3 tickets and confirm if each has been resolved
> * Take a ticket id and run it through the agent team
> * Provide a recap of recent agent events - what the agent said and tools used, then refresh the board
> * Approve payment or purchase after a person selects approve (agents need to continue to only prep the pay, this is where money actually turns into cash).
> * Return the checking balance from "cash_accounts"
> * Reset the database to the og values when I need to refresh the run
>
>
> From backend/ folder start the server with:
> uvicorn main:app --reload --port 8000
>
> Creating the backend at http:localhost:8000 so the frontend dashboard can call these chanels
>
> In "output/harness.md" outline each route in one line (the URL/what it does)

**Follow-up prompt:** None needed so far.

**What was lacking after the first prompt:** Nothing so far.

---

## Problem 8: Agent dashboard

**My prompt:**

> Problem 8 agent dashboard
>
> I need a frontend dashboard in "frontend/" with a react + vite + typescript
>
> The page needs to call the routes we built in problem 7. As a baseline, we need the board to:
>
> * show all 3 tickets
> * give me the option to select one and start the agent team on it
> * show the agent adn what they are communicating/doing as the ticket is run
> * mark the ticket as done when the run finishes
> * provide a summary of what each agent did for the ticket
> * let the human approve the action of pay or purchase when prompted
> * provide the checking balance (post approved pay, it sould decrease)
>
>
> I want this dashboard to be lovely and charming. The layout and vibe should be a real desk an actual person would want to spend time at - so I want creature comforts, a cup of coffee, a window with some sunlight coming through.
>
> Make sure the front end is able to talk with the backend at http://localhost:8000
>
> On the backend, we need vite page origin (probably http://localhost:5173), the browser is allowed to call those routes
>
> the board should start with, "npm run dev" to open the React desk in my browser so I can select my ticket and observe the agents.
>
> Then i need a summary put in "output/design.md" with what I selected for the dashboard vibe, how agents read differently, resolved tickets and cash showed up) and why - including my request to make the space cozy.

**Follow-up prompts:**

> what's happening here?

> let's implement the recommendations

**What was lacking after the first prompt:** The first real run of Ticket 101 showed "Stopped early" for three agents. Accounting had reached its limit of model calls, that stop ended the whole ticket, and Accounting also prepared a rent payment on the wrong ticket. I approved raising the limits, handing control back to Boss when an agent stops, and adding one line to Accounting's prompt.

---

## Problem 9: Resolve the tickets

**My prompt:**

> Problem 9 resolve the ticket
>
> Before testing the agents by running all 3 tickets, we need to reset the databse "data/campus_customs_new.db" for a fresh start
>
> Note the starting cash balance
>
> then push all three tickets through the process until each is closed.
>
> Open "output/desk_tickets.html" from prob 6
>
> for each ticket, add to the actual section from this run - which agents worked, how the delegated, the tools used.

**Follow-up prompts:**

> keep expectations part to compare

> for the cash tab, "output/desk_tickets.html" itemize the cash
>
> * start with the checking balance (once reset)
> * for each ticket - note how cash changed once the ticket was resolved and give the reason
> * ending checking balance - needs to match "cash_accounts" in databse
>
>
> wrong cash math deducts points! even if the board shows all tickets closed.
>
> * "output/resolved_tickets.json" for each ticket: id, last status, brief outcome, what each agent did, any human approvals
> * "output/resolved_board.html" page i can double click with screenshot of the react board for each ticket that has been resolved (101, 102, 103)
>
> Then store real runs to "output/audit_trail.json"
>
> Finish "output/harness.md" to cover the tables, mcp tools, 5 agents, api routes, dashboard and saftey rules

> Yes, make all changes (Recommended)

> Yes, reset and rerun (Recommended)

> What are some approaches we can take to reduce the token need?

> lets Start over: Make the changes, reset, and rerun all three tickets.

> not fully start over

> just reset

> yes Add the token changes, then run with the tighter delegation limits, the briefing tool and the hand-off prompt line, then I will run 102, 101 and 103 to confirm that this uses fewer tokens.
>
> Please make note of this in my homework log, as I know there's a placeholder for follow-up prompts

> Done

> Add the note box (Recommended)

> Offer the 8 in stock (Recommended)

> Do i need to send the email in order to resolve this?

> Okay all three are resolved! now what?

**What was lacking after the first prompt:** My first prompt covered the runs and the Actual sections, but not keeping my Expected sections, the cash itemization, or the final evidence files. The first full run of Ticket 101 also reached its limit because agents kept passing work back and forth and double counted a payment, so I approved a code guard and two prompt lines before rerunning. Ticket 102 then stalled without a rent request, so I approved one more prompt line and a clean rerun in payment order. Ticket 103 then used about 111,000 tokens, so I asked for ways to reduce token use and chose a clean rerun with tighter delegation limits, a single briefing tool, and a prompt line about trusting hand-offs. I reset the database and ran the three tickets from my desk. Total tokens rose from about 169,000 to about 207,000, with only Ticket 103 going down, so the changes did not reduce use overall. After my approvals, Ticket 101 stalled because the agents would not prepare the $8 tee order without authorization, so I added a "Note to the team" box to give them an instruction. I chose to offer the Yale AI Club the 8 hoodies in stock. All three tickets are now resolved, with $152.00 left in checking.

---

## Problem 10: Reflection

**My prompt:**

> Problem 10 reflection
>
> I need to make notes for "output/desk_ticekts.html" and submit a refections tab.
>
> Help me answer in my own vibe and help me include details around the following prompts:
>
> * How would we evaluate the performance of the agents on each ticket and why?
> * For each ticket, how did actual compare to expected plan we wrote earlier?
> * what would have been simpler as one agent with tools, why?
> * describe three new problems campus customs might face that this agent team could solve with the tools we built
> * Describe three new problems campus customs might face that this agent team could not solve with the tools we built, explain the tools and agents we would need to solve them
>
>
> Lastly, tie all the answers to this app, and the three tickets we worked through. Let's leverage the ticket tabs, and Cash tab on the same page as our evidence.

**Follow-up prompts:**

> please give me feedback on my draft above, I need help creating the tools to address the three problems in the last question.

> Save with light fixes (Recommended)

> * I'm adding a line for each on how the team would handle: `check_stock` would confirm the 40 Yale Caps and Customer Service could save_customer_draft
> * Ticket 102 earned an A  because it was pretty straight forward in terms of staying with facilities, and Ticket 103 a B+ because it a pain to sort out.
> * One-agent answer please add Most of the safety came from the tools, not the need for multiple agents.

> Okay let's update with:
>
> * Ticket 102: update to include "because it was pretty straightforward, moving from Facilities to Accounting."
> * "Could solve": Only the Yale Cap has a line so far. The Crest Mug restock and fake rent notice could each use one.
> * help me with the second bullet please

**What was lacking after the first prompt:** I wrote my own answers and needed feedback on them, plus tool ideas for the three problems the team could not solve. Claude placed my answers under the right questions, corrected typos and one fact about which agent prepares payments, and added links to the ticket and Cash tabs.

---

## Problem 11: Submit to GitHub

**My prompt:**

> Problem 11 submit to GitHub
>
> Now we need to push the code to a public repository for the TAs to copy it. I need to submit the repo URL to canvas, and also add it to output/github.url.txt
>
> Please DO NOT publish real .env to github repo. But I need to include both database files under data/ (my og working files).
>
> I need the following layout
>
> README should provide info: copy origional DB to working copy when a clean run is needed, start MCP server, start FastAPI backend, start the react board, reset the DB before the full three ticket run

**Follow-up prompt:** None needed so far.

**What was lacking after the first prompt:** Nothing so far.

---
