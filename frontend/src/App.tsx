import { useMemo, useState } from "react";
import { AGENTS, agentStates } from "./agents";
import { Corkboard } from "./components/Corkboard";
import { Notebook } from "./components/Notebook";
import { Passbook } from "./components/Passbook";
import { Clock, Mug, phaseOf, Plant, Window } from "./components/Scenery";
import { Tray } from "./components/Tray";
import { useDesk } from "./useDesk";

export default function App() {
  const desk = useDesk();
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const ticket = desk.tickets.find((item) => item.id === selectedId) ?? null;
  const events = useMemo(
    () => desk.events.filter((event) => event.ticket_id === selectedId),
    [desk.events, selectedId],
  );

  const pending = desk.board.filter((item) => item.status === "pending");
  const pendingTickets = new Set(pending.map((item) => item.ticket_id));
  const drafts = desk.board.filter(
    (item) => item.kind === "customer_draft" && item.ticket_id === selectedId,
  );
  const stateOf = agentStates(events, desk.active === selectedId);

  return (
    <div className={`room sun-${phaseOf(ticket?.created_at)}`}>
      <div className="sunbeam" aria-hidden="true" />
      <header className="wall">
        <div className="window-wrap">
          <Window />
          <div className="sill"><Plant /></div>
        </div>
        <div className="wall-middle">
          <h1>Campus Customs back office</h1>
          <Corkboard
            tickets={desk.tickets}
            selectedId={selectedId}
            activeId={desk.active}
            pendingTickets={pendingTickets}
            onSelect={setSelectedId}
          />
        </div>
        <Clock time={ticket?.created_at} />
      </header>

      <main className="desk">
        {!desk.connected && (
          <p className="alert" role="alert">
            The desk can't reach the backend. Start it on port 8000, and this page will reconnect.
          </p>
        )}
        {desk.problem && <p className="alert" role="alert">{desk.problem}</p>}
        <div className="desk-grid">
          <aside className="left-side">
            <Mug steaming={desk.active !== null} />
            <ul className="team" aria-label="The team">
              {AGENTS.map((agent) => {
                const state = stateOf(agent.id);
                return (
                  <li key={agent.id} className={`nameplate agent-${agent.id} ${state}`}>
                    <strong>{agent.name}</strong>
                    <span>{state === "resting" ? agent.job : state === "working" ? "Working" : "Finished"}</span>
                  </li>
                );
              })}
            </ul>
          </aside>
          <Notebook
            ticket={ticket}
            events={events}
            drafts={drafts}
            running={desk.active === selectedId && desk.active !== null}
            busy={desk.active !== null}
            hasPending={selectedId !== null && pendingTickets.has(selectedId)}
            onStart={(note) => selectedId !== null && void desk.startTicket(selectedId, note)}
          />
          <aside className="right-side">
            <Tray items={pending} onDecide={(id, decision, name) => void desk.decide(id, decision, name)} />
            <Passbook cash={desk.cash} board={desk.board} busy={desk.active !== null} onReset={() => void desk.reset()} />
          </aside>
        </div>
      </main>
    </div>
  );
}
