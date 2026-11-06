"""Quick check that all five agents run with their real prompts.

Boss delegates a small question to each of the other agents. No ticket is
worked and nothing is prepared. The run appears in the audit trail as ticket 0.
Run it from the project root: python backend/check_team.py
"""

import asyncio
import json

import config
from team import ROLES, run_ticket

TASK = (
    "This is a team check, not a real ticket. Delegate one short task to each of "
    "inventory, accounting, facilities, and customer_service: ask each one to say "
    "what its job is in one sentence. Tell them not to prepare anything, change "
    "anything, or delegate. You must not call update_ticket. Set ticket_status to "
    "open in your report."
)


def agents_that_ran(run_id: str) -> set[str]:
    trail = json.loads(config.AUDIT_PATH.read_text(encoding="utf-8"))
    return {
        entry["agent"]
        for entry in trail
        if entry["run_id"] == run_id and entry["event"] == "run_end"
    }


async def main() -> None:
    outcome = await run_ticket(0, task=TASK)
    finished = agents_that_ran(outcome.run_id)

    print(f"Model: {config.MODEL_NAME}")
    if outcome.report:
        print(f"Boss report: {outcome.report.summary}")
    if outcome.stopped_reason:
        print(f"Stopped: {outcome.stopped_reason}")
    print(f"Agents that finished: {', '.join(sorted(finished))}")
    print(f"Model calls: {outcome.model_calls}")
    print(f"Tokens used: {outcome.total_tokens}")
    print(f"Delegations: {outcome.delegations}")

    if finished == set(ROLES):
        print("PASS: all five agents ran, and the audit trail recorded them.")
    else:
        print(f"NOT YET: missing {', '.join(sorted(set(ROLES) - finished))}")


if __name__ == "__main__":
    asyncio.run(main())
