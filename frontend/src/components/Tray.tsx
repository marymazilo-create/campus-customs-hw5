import { useState } from "react";
import type { BoardItem } from "../types";

interface Props {
  items: BoardItem[];
  onDecide: (id: number, decision: "approve" | "reject", name: string) => void;
}

const money = (value: number) =>
  value.toLocaleString("en-US", { style: "currency", currency: "USD" });

function describe(item: BoardItem) {
  const details = item.details;
  if (item.kind === "payment_request") {
    return {
      title: `Pay ${details.payee}`,
      body: String(details.description),
      note: `Due ${details.due_date}`,
      action: `Approve and pay ${money(item.amount ?? 0)}`,
    };
  }
  if (item.kind === "purchase_order") {
    const blockers = details.blocked_by_open_invoices as number[];
    return {
      title: `Order from ${details.payee}`,
      body: `${details.qty} × ${details.name}, size ${details.size}, ${money(Number(details.unit_cost))} each`,
      note: blockers.length
        ? `On hold until invoice ${blockers.join(", ")} is paid`
        : `Expected ${details.expected_arrival}`,
      action: `Approve and pay ${money(item.amount ?? 0)}`,
    };
  }
  return {
    title: `Discount of ${details.discount_pct}%`,
    body: `${details.qty} × ${details.sku} at ${money(Number(details.discounted_price))} instead of ${money(Number(details.list_price))}`,
    note: details.below_cost
      ? "This price is below cost"
      : `Leaves ${money(Number(details.margin_per_unit_after))} margin per unit`,
    action: "Approve discount",
  };
}

function savedName() {
  try {
    return localStorage.getItem("desk-signature") ?? "";
  } catch {
    return "";
  }
}

export function Tray({ items, onDecide }: Props) {
  const [name, setName] = useState(savedName);

  const changeName = (value: string) => {
    setName(value);
    try {
      localStorage.setItem("desk-signature", value);
    } catch {
      // The name just won't be remembered next time.
    }
  };

  return (
    <section className="tray" aria-label="Requests waiting for your signature">
      <h2>In-tray</h2>
      {items.length === 0 && <p className="tray-empty">Nothing needs your signature.</p>}
      {items.length > 0 && (
        <label className="signature">
          Signing as
          <input value={name} onChange={(event) => changeName(event.target.value)} placeholder="Your name" />
        </label>
      )}
      {items.map((item) => {
        const slip = describe(item);
        return (
          <article key={item.id} className="request">
            <h3>{slip.title}</h3>
            <p>{slip.body}</p>
            <p className="request-note">{slip.note}</p>
            <div className="request-actions">
              <button className="approve" disabled={!name.trim()} onClick={() => onDecide(item.id, "approve", name.trim())}>
                {slip.action}
              </button>
              <button className="decline" disabled={!name.trim()} onClick={() => onDecide(item.id, "reject", name.trim())}>
                Decline
              </button>
            </div>
          </article>
        );
      })}
    </section>
  );
}
