export type AgentName =
  | "boss"
  | "inventory"
  | "accounting"
  | "facilities"
  | "customer_service";

export interface Ticket {
  id: number;
  type: string;
  requester: string;
  subject: string;
  status: "open" | "in_progress" | "waiting_on_human" | "resolved";
  created_at: string;
  resolved: boolean;
}

export interface TicketList {
  tickets: Ticket[];
  running_ticket: number | null;
}

export interface BoardItem {
  id: number;
  kind: "payment_request" | "purchase_order" | "discount_request" | "customer_draft";
  ticket_id: number;
  status: "pending" | "paid" | "approved" | "rejected" | "draft";
  amount: number | null;
  details: Record<string, unknown>;
  created_by: string;
  decided_by: string | null;
}

export interface AuditEvent {
  timestamp: string;
  run_id: string;
  ticket_id: number;
  agent: AgentName | "human";
  depth: number;
  step: number;
  event: string;
  tool: string | null;
  tool_call_id: string | null;
  args: Record<string, unknown> | null;
  result: string | null;
  text: string | null;
}

export interface Cash {
  found: boolean;
  balance: number;
  pending_requests_total: number;
  balance_after_pending: number;
}

export interface AgentReport {
  summary: string;
  facts_used: string[];
  actions_taken: string[];
  needs_human: string[];
  ticket_status: string;
}
