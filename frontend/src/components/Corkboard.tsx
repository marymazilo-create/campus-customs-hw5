import type { Ticket } from "../types";

interface Props {
  tickets: Ticket[];
  selectedId: number | null;
  activeId: number | null;
  pendingTickets: Set<number>;
  onSelect: (id: number) => void;
}

const LABELS: Record<string, string> = {
  customer_order: "Customer order",
  rent_notice: "Rent notice",
  price_override: "Price request",
};

function arrived(createdAt: string) {
  const [hours, minutes] = createdAt.slice(11, 16).split(":").map(Number);
  const suffix = hours < 12 ? "AM" : "PM";
  return `${hours % 12 || 12}:${String(minutes).padStart(2, "0")} ${suffix}`;
}

function stateOf(ticket: Ticket, activeId: number | null, hasPending: boolean) {
  if (ticket.id === activeId) return "The team is on it";
  if (hasPending) return "Needs your signature";
  if (ticket.status === "open") return "Not started";
  return "Ready to go back to the team";
}

export function Corkboard({ tickets, selectedId, activeId, pendingTickets, onSelect }: Props) {
  return (
    <div className="corkboard" aria-label="Open tickets">
      {tickets.map((ticket) => {
        const pending = pendingTickets.has(ticket.id);
        return (
          <button
            key={ticket.id}
            className={`ticket ${selectedId === ticket.id ? "selected" : ""} ${ticket.id === activeId ? "active" : ""}`}
            aria-pressed={selectedId === ticket.id}
            onClick={() => onSelect(ticket.id)}
          >
            <span className="pin" aria-hidden="true" />
            <span className="ticket-number">No. {ticket.id}</span>
            <span className="ticket-subject">{ticket.subject}</span>
            <span className="ticket-line">{ticket.requester}</span>
            <span className="ticket-line">
              {LABELS[ticket.type] ?? ticket.type}, {arrived(ticket.created_at)}
            </span>
            {ticket.resolved ? (
              <span className="stamp">Resolved</span>
            ) : (
              <span className="ticket-state">{stateOf(ticket, activeId, pending)}</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
