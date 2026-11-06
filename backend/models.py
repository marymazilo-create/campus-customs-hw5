"""Data types shared by the Campus Customs agents."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Role = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]
TicketStatus = Literal["open", "in_progress", "waiting_on_human", "resolved"]
AuditEvent = Literal[
    "run_start",
    "model_response",
    "tool_call",
    "tool_result",
    "delegation",
    "delegation_refused",
    "run_end",
    "run_error",
    "human_decision",
    "database_reset",
]


class AgentReport(BaseModel):
    """What every agent hands back when its turn ends."""

    summary: str = Field(description="What this agent found and did, in plain language.")
    facts_used: list[str] = Field(
        default_factory=list,
        description="Facts that came from MCP tools, each with its source tool.",
    )
    actions_taken: list[str] = Field(
        default_factory=list,
        description="Items prepared or tickets updated. Empty if nothing changed.",
    )
    needs_human: list[str] = Field(
        default_factory=list,
        description="Decisions or approvals that only a person can make.",
    )
    ticket_status: TicketStatus = Field(description="Where the ticket stands now.")


class TicketOutcome(BaseModel):
    """The result of one full ticket run."""

    run_id: str
    ticket_id: int
    completed: bool
    report: Optional[AgentReport] = None
    stopped_reason: Optional[str] = None
    model_calls: int
    total_tokens: int
    delegations: int


class AuditEntry(BaseModel):
    """One row in output/audit_trail.json."""

    timestamp: str
    run_id: str
    ticket_id: int
    agent: Role | Literal["human"]
    delegated_by: Optional[Role] = None
    depth: int
    step: int
    event: AuditEvent
    model: Optional[str] = None
    tool: Optional[str] = None
    tool_call_id: Optional[str] = None
    args: Optional[Any] = None
    result: Optional[Any] = None
    text: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class RunRequest(BaseModel):
    """Sent by the dashboard when a ticket starts or goes back to the team."""

    note: Optional[str] = Field(default=None, max_length=1000)


class HumanDecision(BaseModel):
    """Sent by the dashboard when a person approves or rejects a board item."""

    decided_by: str = Field(min_length=1, description="The name of the person deciding.")
