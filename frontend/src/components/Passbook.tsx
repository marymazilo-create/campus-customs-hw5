import { useState } from "react";
import type { BoardItem, Cash } from "../types";

interface Props {
  cash: Cash | null;
  board: BoardItem[];
  busy: boolean;
  onReset: () => void;
}

const money = (value: number) =>
  value.toLocaleString("en-US", { style: "currency", currency: "USD" });

export function Passbook({ cash, board, busy, onReset }: Props) {
  const [confirming, setConfirming] = useState(false);
  const paid = board.filter((item) => item.status === "paid");
  const spent = paid.reduce((total, item) => total + (item.amount ?? 0), 0);
  const opening = cash ? cash.balance + spent : 0;
  let running = opening;

  return (
    <section className="passbook" aria-label="Checking account">
      <h2>Checking</h2>
      <p className="balance">{cash ? money(cash.balance) : "..."}</p>
      <table>
        <tbody>
          <tr>
            <td>Opening balance</td>
            <td />
            <td>{money(opening)}</td>
          </tr>
          {paid.map((item) => {
            running -= item.amount ?? 0;
            return (
              <tr key={item.id} className="entry">
                <td>{String(item.details.payee)}</td>
                <td>-{money(item.amount ?? 0)}</td>
                <td>{money(running)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {cash && cash.pending_requests_total > 0 && (
        <p className={cash.balance_after_pending < 0 ? "pending short" : "pending"}>
          {money(cash.pending_requests_total)} waiting for approval leaves{" "}
          {cash.balance_after_pending < 0 ? "the shop short by " : ""}
          {money(Math.abs(cash.balance_after_pending))}
        </p>
      )}
      <div className="reset">
        {!confirming && (
          <button onClick={() => setConfirming(true)} disabled={busy}>
            Start the day over
          </button>
        )}
        {confirming && (
          <>
            <span>Restore the original shop data?</span>
            <button onClick={() => { setConfirming(false); onReset(); }}>Restore</button>
            <button onClick={() => setConfirming(false)}>Keep working</button>
          </>
        )}
      </div>
    </section>
  );
}
