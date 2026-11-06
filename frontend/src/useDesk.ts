import { useCallback, useEffect, useMemo, useState } from "react";
import * as api from "./api";
import type { AuditEvent, BoardItem, Cash, Ticket } from "./types";

const POLL_RUNNING_MS = 1200;
const POLL_IDLE_MS = 8000;

export function useDesk() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [runningTicket, setRunningTicket] = useState<number | null>(null);
  const [starting, setStarting] = useState<number | null>(null);
  const [board, setBoard] = useState<BoardItem[]>([]);
  const [cash, setCash] = useState<Cash | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [connected, setConnected] = useState(true);
  const [problem, setProblem] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [ticketList, boardItems, balance, trail] = await Promise.all([
        api.getTickets(),
        api.getBoard(),
        api.getCash(),
        api.getEvents(),
      ]);
      setTickets(ticketList.tickets);
      setRunningTicket(ticketList.running_ticket);
      setBoard(boardItems);
      setCash(balance);
      setEvents(trail);
      setConnected(true);
    } catch {
      setConnected(false);
    }
  }, []);

  const active = runningTicket ?? starting;

  useEffect(() => {
    void refresh();
    const timer = setInterval(() => void refresh(), active ? POLL_RUNNING_MS : POLL_IDLE_MS);
    return () => clearInterval(timer);
  }, [active, refresh]);

  const startTicket = useCallback(
    async (ticketId: number, note: string) => {
      setProblem(null);
      setStarting(ticketId);
      try {
        const outcome = await api.runTicket(ticketId, note);
        if (outcome.stopped_reason) setProblem(`The run stopped: ${outcome.stopped_reason}`);
      } catch (error) {
        setProblem((error as Error).message);
      }
      setStarting(null);
      await refresh();
    },
    [refresh],
  );

  const decide = useCallback(
    async (itemId: number, decision: "approve" | "reject", name: string) => {
      setProblem(null);
      try {
        await api.decide(itemId, decision, name);
      } catch (error) {
        setProblem((error as Error).message);
      }
      await refresh();
    },
    [refresh],
  );

  const reset = useCallback(async () => {
    setProblem(null);
    try {
      await api.resetDesk();
    } catch (error) {
      setProblem((error as Error).message);
    }
    await refresh();
  }, [refresh]);

  // Everything before the latest reset belongs to an earlier run of the desk.
  const currentEvents = useMemo(() => {
    const lastReset = events.map((event) => event.event).lastIndexOf("database_reset");
    return events.slice(lastReset + 1);
  }, [events]);

  return {
    tickets,
    active,
    board,
    cash,
    events: currentEvents,
    connected,
    problem,
    startTicket,
    decide,
    reset,
  };
}
