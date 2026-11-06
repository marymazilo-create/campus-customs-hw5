import type { AgentName, AgentReport, AuditEvent } from "./types";

export const AGENTS: { id: AgentName; name: string; job: string }[] = [
  { id: "boss", name: "Boss", job: "Makes the calls" },
  { id: "inventory", name: "Inventory", job: "Counts the stock" },
  { id: "accounting", name: "Accounting", job: "Minds the cash" },
  { id: "facilities", name: "Facilities", job: "Keeps the lease" },
  { id: "customer_service", name: "Customer Service", job: "Writes to customers" },
];

const AGENT_NAMES = Object.fromEntries(AGENTS.map((agent) => [agent.id, agent.name]));

export const agentName = (id: string) => AGENT_NAMES[id] ?? id;

const TOOL_LABELS: Record<string, string> = {
  get_shop_date: "Checked the shop date",
  list_open_tickets: "Looked over the open tickets",
  get_ticket: "Read the ticket",
  check_stock: "Counted the stock",
  list_vendors: "Went through the vendor list",
  get_invoice: "Pulled the invoice",
  get_open_invoices: "Checked for unpaid invoices",
  get_pricing: "Looked up cost and price",
  get_cash_balance: "Checked the cash",
  get_lease: "Pulled the lease",
  list_board_items: "Checked what's on the board",
  prepare_payment: "Prepared a payment for your approval",
  prepare_purchase_order: "Prepared a purchase order for your approval",
  prepare_discount_request: "Prepared a discount request for your approval",
  save_customer_draft: "Saved a draft message",
  update_ticket: "Updated the ticket",
};

export interface NoteLine {
  key: string;
  agent: AgentName;
  kind: "handoff" | "tool" | "report" | "problem";
  text: string;
}

export function parseReport(result: string | null): AgentReport | null {
  try {
    return result ? (JSON.parse(result) as AgentReport) : null;
  } catch {
    return null;
  }
}

function toolDetail(args: AuditEvent["args"]): string {
  if (!args) return "";
  const values = ["sku", "size", "qty", "invoice_id", "lease_id", "vendor_id"]
    .filter((field) => args[field] !== undefined)
    .map((field) => String(args[field]));
  return values.length ? ` (${values.join(", ")})` : "";
}

export function eventsToNotes(events: AuditEvent[]): NoteLine[] {
  const notes: NoteLine[] = [];
  for (const event of events) {
    if (event.agent === "human") continue;
    const key = `${event.run_id}-${event.agent}-${event.depth}-${event.step}`;
    if (event.event === "delegation") {
      const to = agentName(String(event.args?.to ?? ""));
      const task = String(event.args?.task ?? "");
      notes.push({ key, agent: event.agent, kind: "handoff", text: `To ${to}: ${task}` });
    } else if (event.event === "tool_call" && event.tool && event.tool !== "delegate") {
      const label = TOOL_LABELS[event.tool] ?? event.tool;
      notes.push({ key, agent: event.agent, kind: "tool", text: label + toolDetail(event.args) });
    } else if (event.event === "run_end") {
      const report = parseReport(event.result);
      if (report) notes.push({ key, agent: event.agent, kind: "report", text: report.summary });
    } else if (event.event === "run_error") {
      const hitLimit = event.text?.startsWith("LoopLimitReached");
      const text = hitLimit
        ? "Reached its limit of model calls and handed back."
        : "Stopped early. See the audit trail.";
      const repeated = notes.some((note) => note.kind === "problem" && note.text === text);
      if (!repeated) notes.push({ key, agent: event.agent, kind: "problem", text });
    }
  }
  return notes;
}

export interface AgentSummary {
  id: AgentName;
  reports: AgentReport[];
  tools: string[];
}

export function summarize(events: AuditEvent[]): AgentSummary[] {
  return AGENTS.map(({ id }) => {
    const own = events.filter((event) => event.agent === id);
    const reports = own
      .filter((event) => event.event === "run_end")
      .map((event) => parseReport(event.result))
      .filter((report): report is AgentReport => report !== null);
    const tools = [
      ...new Set(
        own
          .filter((event) => event.event === "tool_call" && event.tool !== "delegate")
          .map((event) => event.tool ?? ""),
      ),
    ];
    return { id, reports, tools };
  }).filter((summary) => summary.reports.length > 0 || summary.tools.length > 0);
}

export type AgentState = "resting" | "working" | "finished";

export function agentStates(events: AuditEvent[], running: boolean) {
  const open = new Map<string, number>();
  const seen = new Set<string>();
  for (const event of events) {
    if (event.event === "run_start") {
      open.set(event.agent, (open.get(event.agent) ?? 0) + 1);
      seen.add(event.agent);
    }
    if (event.event === "run_end" || event.event === "run_error") {
      open.set(event.agent, Math.max((open.get(event.agent) ?? 1) - 1, 0));
    }
  }
  return (id: AgentName): AgentState => {
    if (running && (open.get(id) ?? 0) > 0) return "working";
    return seen.has(id) ? "finished" : "resting";
  };
}
