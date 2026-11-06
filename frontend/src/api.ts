import type { AuditEvent, BoardItem, Cash, TicketList } from "./types";

const API = "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof body.detail === "string" ? body.detail : "Enter your name first.";
    throw new Error(detail);
  }
  return body as T;
}

export const getTickets = () => request<TicketList>("/tickets");

export const getCash = () => request<Cash>("/cash");

export const getBoard = async () =>
  (await request<{ items: BoardItem[] }>("/board")).items;

export const getEvents = async () =>
  (await request<{ events: AuditEvent[] }>("/events?limit=1000")).events;

export const runTicket = (ticketId: number, note: string) =>
  request<{ stopped_reason: string | null }>(`/tickets/${ticketId}/run`, {
    method: "POST",
    body: JSON.stringify({ note }),
  });

export const decide = (
  itemId: number,
  decision: "approve" | "reject",
  decidedBy: string,
) =>
  request<unknown>(`/board/${itemId}/${decision}`, {
    method: "POST",
    body: JSON.stringify({ decided_by: decidedBy }),
  });

export const resetDesk = () => request<unknown>("/reset", { method: "POST" });
