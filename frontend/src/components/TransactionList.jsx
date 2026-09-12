import {
  explorerFor,
  normalizeDecision,
  numberValue,
  riskFromDecision
} from "../lib/format.js";

function cardMeta(decision) {
  const normalized = normalizeDecision(decision);
  if (normalized === "APPROVE") {
    return { status: "APPROVED", cardClass: "approved", icon: "✓" };
  }
  if (normalized === "REVIEW") {
    return { status: "REVIEW", cardClass: "review", icon: "!" };
  }
  return { status: "BLOCKED", cardClass: "blocked", icon: "×" };
}

export default function TransactionList({ transactions, onRefresh }) {
  return (
    <section className="section">
      <div className="section-heading">
        <div>
          <div className="eyebrow">AUDIT TRAIL</div>
          <h2>Transaction History</h2>
        </div>
        <button className="refresh-btn" type="button" onClick={onRefresh}>
          ↻ Refresh
        </button>
      </div>

      <div className="transaction-list">
        {transactions.length === 0 ? (
          <div className="empty-state">No transactions recorded yet.</div>
        ) : (
          transactions.slice(0, 20).map((transaction, index) => {
            const meta = cardMeta(transaction.decision);
            const explorer = explorerFor(transaction);
            const risk = String(
              transaction.risk_level ?? riskFromDecision(transaction.decision)
            ).toUpperCase();

            return (
              <div
                className={`transaction-card ${meta.cardClass}`}
                key={transaction.transaction_id ?? `${transaction.service}-${index}`}
              >
                <div className="transaction-icon">{meta.icon}</div>
                <div className="transaction-info">
                  <h3>{transaction.service ?? "Unknown Service"}</h3>
                  <p>{transaction.payment_protocol ?? "x402"}</p>
                </div>
                <div className="transaction-trust">
                  <strong>{numberValue(transaction.trust_score)}/100</strong>
                  <span>{risk} RISK</span>
                </div>
                <div className="transaction-amount">
                  <strong>${numberValue(transaction.amount).toFixed(3)}</strong>
                  <span>{meta.status}</span>
                </div>
                {explorer ? (
                  <div className="transaction-chain">
                    <a href={explorer} target="_blank" rel="noopener noreferrer">
                      {transaction.blockchain_tx_id}
                    </a>
                  </div>
                ) : null}
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}
