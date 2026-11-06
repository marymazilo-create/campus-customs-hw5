"""The Campus Customs agent team.

Five PydanticAI agents, each with its own prompt and its own MCP tools:
  boss, inventory, accounting, facilities, customer_service.

Shop facts come only from the MCP server. Any agent can delegate to any
other agent with the delegate tool, and every loop step goes to the audit
trail. Each ticket starts with Boss.
"""

import json
import uuid
from dataclasses import dataclass, field
from typing import Optional, get_args

from pydantic_ai import Agent, NativeOutput, RunContext
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.messages import (
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.usage import RunUsage, UsageLimits

import audit
import config
from models import AgentReport, Role, TicketOutcome

ROLES: tuple[Role, ...] = get_args(Role)

# Only a person can reach these. They are removed from every agent's tools.
HUMAN_ONLY_TOOLS = {"pay", "decide_request"}

AGENT_TOOLS: dict[Role, set[str]] = {
    "boss": {
        "get_ticket_briefing",
        "list_open_tickets",
        "list_board_items",
        "update_ticket",
    },
    "inventory": {
        "get_ticket_briefing",
        "check_stock",
        "list_vendors",
        "get_invoice",
        "get_open_invoices",
        "get_pricing",
    },
    "accounting": {
        "get_ticket_briefing",
        "list_vendors",
        "get_invoice",
        "get_open_invoices",
        "get_pricing",
        "get_cash_balance",
        "get_lease",
        "list_board_items",
        "prepare_payment",
        "prepare_purchase_order",
        "prepare_discount_request",
    },
    "facilities": {
        "get_ticket_briefing",
        "get_lease",
    },
    "customer_service": {
        "get_ticket_briefing",
        "check_stock",
        "list_board_items",
        "save_customer_draft",
    },
}


class LoopLimitReached(RuntimeError):
    """An agent used up its model calls for this run."""


@dataclass
class TicketRun:
    """Shared state for one ticket, across all agents working on it."""

    ticket_id: int
    team: dict[Role, Agent] = field(default_factory=dict)
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    usage: RunUsage = field(default_factory=RunUsage)
    delegations: int = 0
    tasks_seen: set[tuple[str, str]] = field(default_factory=set)


@dataclass
class AgentDeps:
    """What one agent knows about its place in the run."""

    run: TicketRun
    role: Role
    depth: int
    delegated_by: Optional[Role] = None
    chain: tuple[Role, ...] = ()
    steps: int = 0

    def audit(self, event: str, **fields) -> None:
        self.steps += 1
        audit.record(
            run_id=self.run.run_id,
            ticket_id=self.run.ticket_id,
            agent=self.role,
            delegated_by=self.delegated_by,
            depth=self.depth,
            step=self.steps,
            event=event,
            **fields,
        )


def load_prompt(role: Role) -> str:
    path = config.PROMPTS_DIR / f"{role}.md"
    if not path.exists():
        raise FileNotFoundError(f"Missing agent prompt: {path}")
    return path.read_text(encoding="utf-8")


async def delegate(ctx: RunContext[AgentDeps], to: Role, task: str) -> str:
    """Ask another agent to do a task and return its report.

    Use this when the work belongs to another agent. Give a specific task
    with the IDs, SKUs, and quantities that agent needs.
    """
    deps = ctx.deps
    run = deps.run
    task_key = (to, " ".join(task.lower().split()))

    refusal = None
    if to == deps.role:
        refusal = "An agent cannot delegate to itself."
    elif to in deps.chain:
        refusal = f"{to} is already waiting for this work. Report back instead."
    elif deps.depth >= config.MAX_DELEGATION_DEPTH:
        refusal = "Delegation depth limit reached. Finish with what you have."
    elif run.delegations >= config.MAX_DELEGATIONS_PER_TICKET:
        refusal = "Delegation limit for this ticket reached. Finish with what you have."
    elif task_key in run.tasks_seen:
        refusal = f"{to} already received this task. Use its earlier report."

    if refusal:
        deps.audit("delegation_refused", tool="delegate", args={"to": to, "task": task}, text=refusal)
        return json.dumps({"refused": True, "reason": refusal})

    run.delegations += 1
    run.tasks_seen.add(task_key)
    deps.audit("delegation", tool="delegate", args={"to": to, "task": task})
    try:
        report = await run_agent(to, task, run, deps.depth + 1, deps.role, deps.chain)
    except LoopLimitReached as error:
        # One agent stopping should not end the ticket. Hand control back.
        return json.dumps(
            {
                "stopped": True,
                "reason": f"{error} Its finished work is on the board. Check before asking again.",
            }
        )
    return report.model_dump_json()


def build_agent(role: Role, model, server: MCPToolset) -> Agent:
    """Create one agent with its prompt, its MCP tools, and the delegate tool."""
    allowed = AGENT_TOOLS[role] - HUMAN_ONLY_TOOLS
    return Agent(
        model,
        name=role,
        deps_type=AgentDeps,
        instructions=load_prompt(role),
        output_type=NativeOutput(AgentReport),
        tools=[delegate],
        toolsets=[server.filtered(lambda ctx, tool: tool.name in allowed)],
    )


def _audit_model_response(deps: AgentDeps, response) -> None:
    deps.audit(
        "model_response",
        text="\n".join(p.content for p in response.parts if isinstance(p, TextPart)) or None,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    for part in response.parts:
        if isinstance(part, ToolCallPart):
            deps.audit(
                "tool_call",
                tool=part.tool_name,
                tool_call_id=part.tool_call_id,
                args=part.args_as_dict(),
            )


def _audit_tool_results(deps: AgentDeps, request) -> None:
    for part in request.parts:
        if isinstance(part, ToolReturnPart):
            deps.audit(
                "tool_result",
                tool=part.tool_name,
                tool_call_id=part.tool_call_id,
                result=part.model_response_str(),
            )
        elif isinstance(part, RetryPromptPart) and part.tool_name:
            deps.audit(
                "tool_result",
                tool=part.tool_name,
                tool_call_id=part.tool_call_id,
                result=f"Retry requested: {part.model_response()}",
            )


async def run_agent(
    role: Role,
    task: str,
    run: TicketRun,
    depth: int = 0,
    delegated_by: Optional[Role] = None,
    waiting: tuple[Role, ...] = (),
) -> AgentReport:
    """Run one agent's loop, recording each model response and tool result."""
    deps = AgentDeps(
        run=run,
        role=role,
        depth=depth,
        delegated_by=delegated_by,
        chain=(*waiting, role),
    )
    limits = UsageLimits(
        request_limit=config.MAX_MODEL_CALLS_PER_TICKET,
        total_tokens_limit=config.MAX_TOKENS_PER_TICKET,
    )
    deps.audit("run_start", text=task)
    model_calls = 0

    try:
        async with run.team[role].iter(
            task, deps=deps, usage=run.usage, usage_limits=limits
        ) as agent_run:
            async for node in agent_run:
                if Agent.is_model_request_node(node):
                    _audit_tool_results(deps, node.request)
                elif Agent.is_call_tools_node(node):
                    model_calls += 1
                    _audit_model_response(deps, node.model_response)
                    if model_calls >= config.MAX_MODEL_CALLS_PER_AGENT_RUN and any(
                        isinstance(part, ToolCallPart)
                        for part in node.model_response.parts
                    ):
                        raise LoopLimitReached(
                            f"{role} reached {config.MAX_MODEL_CALLS_PER_AGENT_RUN} model calls."
                        )
        report = agent_run.result.output
    except Exception as error:
        deps.audit("run_error", text=f"{type(error).__name__}: {error}")
        raise

    deps.audit("run_end", result=report.model_dump_json())
    return report


async def run_ticket(
    ticket_id: int,
    model=None,
    task: Optional[str] = None,
) -> TicketOutcome:
    """Work one ticket, starting with Boss."""
    model = model or config.build_model()
    run = TicketRun(ticket_id=ticket_id)
    server = MCPToolset(config.MCP_SERVER_PATH)
    run.team = {role: build_agent(role, model, server) for role in ROLES}

    report = None
    stopped_reason = None
    task = task or (
        f"Work ticket {ticket_id}. Read it, get the facts from your tools, "
        "delegate work to the right agents, and report where it stands."
    )
    try:
        async with server:
            report = await run_agent("boss", task, run)
    except UsageLimitExceeded:
        stopped_reason = (
            "This ticket reached its limit of model calls or tokens. "
            "Finished work is on the board."
        )
    except LoopLimitReached as error:
        stopped_reason = str(error)

    return TicketOutcome(
        run_id=run.run_id,
        ticket_id=ticket_id,
        completed=report is not None,
        report=report,
        stopped_reason=stopped_reason,
        model_calls=run.usage.requests,
        total_tokens=run.usage.total_tokens,
        delegations=run.delegations,
    )
