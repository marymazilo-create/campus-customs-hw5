import { useEffect, useRef, useState } from "react";
import { agentName, eventsToNotes, summarize } from "../agents";
import type { AuditEvent, BoardItem, Ticket } from "../types";

interface Props {
  ticket: Ticket | null;
  events: AuditEvent[];
  drafts: BoardItem[];
  running: boolean;
  busy: boolean;
  hasPending: boolean;
  onStart: (note: string) => void;
}

function startLabel(ticket: Ticket) {
  return ticket.status === "open" ? "Start the team" : "Send back to the team";
}

export function Notebook({ ticket, events, drafts, running, busy, hasPending, onStart }: Props) {
  const notes = eventsToNotes(events);
  const summaries = summarize(events);
  const feed = useRef<HTMLOListElement>(null);
  const [note, setNote] = useState("");
  const canSendBack = ticket !== null && ticket.status !== "open" && !ticket.resolved && !hasPending;

  const start = () => {
    onStart(note);
    setNote("");
  };

  useEffect(() => {
    const list = feed.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [notes.length]);

  return (
    <section className="notebook" aria-label="Ticket notebook">
      <div className="page page-left">
        <div className="page-head">
          <h2>{ticket ? `Notes on ticket ${ticket.id}` : "Today's notes"}</h2>
          {ticket && !ticket.resolved && (
            <button className="start" onClick={start} disabled={busy || hasPending}>
              {running ? "Team at work" : startLabel(ticket)}
            </button>
          )}
        </div>
        {!ticket && <p className="blank-page">Pick a ticket from the board to open its notes.</p>}
        {ticket && hasPending && !running && (
          <p className="hint">Sign or decline the waiting requests, then the team can carry on.</p>
        )}
        {canSendBack && !running && (
          <label className="team-note">
            Note to the team
            <textarea
              rows={2}
              maxLength={1000}
              value={note}
              placeholder="Optional: tell Boss what you've decided"
              onChange={(event) => setNote(event.target.value)}
            />
          </label>
        )}
        {ticket && notes.length === 0 && !running && (
          <p className="blank-page">Nobody has touched this ticket yet.</p>
        )}
        {ticket && notes.length === 0 && running && (
          <p className="blank-page">Boss is reading the ticket.</p>
        )}
        <ol className="feed" ref={feed} aria-live="polite">
          {notes.map((note) => (
            <li key={note.key} className={`note agent-${note.agent} note-${note.kind}`}>
              <span className="note-who">{agentName(note.agent)}</span>
              <span className="note-text">{note.text}</span>
            </li>
          ))}
        </ol>
      </div>
      <div className="page page-right">
        <h2>What each agent did</h2>
        {ticket && summaries.length === 0 && (
          <p className="blank-page">A summary from each agent lands here when it finishes.</p>
        )}
        {!ticket && <p className="blank-page">Summaries appear here for the ticket you pick.</p>}
        <div className="summaries">
          {summaries.map((summary) => (
            <article key={summary.id} className={`slip agent-${summary.id}`}>
              <h3>{agentName(summary.id)}</h3>
              {summary.reports.map((report, index) => (
                <p key={index}>{report.summary}</p>
              ))}
              {summary.reports.length === 0 && <p>Still working.</p>}
            </article>
          ))}
          {drafts.map((draft) => (
            <article key={draft.id} className="draft">
              <h3>Draft to {String(draft.details.to)}</h3>
              <p>{String(draft.details.message)}</p>
              <small>Not sent. A person decides what happens to it.</small>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
