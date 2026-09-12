import { normalizeDecision } from "../lib/format.js";

export default function Dashboard({ transactions }) {
  let approved = 0;
  let review = 0;
  let blocked = 0;

  transactions.forEach((transaction) => {
    const decision = normalizeDecision(transaction.decision);
    if (decision === "APPROVE") approved += 1;
    else if (decision === "REVIEW") review += 1;
    else if (decision === "BLOCK") blocked += 1;
  });

  return (
    <section className="section">
      <div className="section-heading">
        <div>
          <div className="eyebrow">SECURITY TELEMETRY</div>
          <h2>Transaction Dashboard</h2>
        </div>
      </div>
      <div className="dashboard-grid">
        <div className="dashboard-card">
          <span>TOTAL TRANSACTIONS</span>
          <strong>{transactions.length}</strong>
        </div>
        <div className="dashboard-card success-card">
          <span>APPROVED</span>
          <strong>{approved}</strong>
        </div>
        <div className="dashboard-card warning-card">
          <span>REVIEW</span>
          <strong>{review}</strong>
        </div>
        <div className="dashboard-card danger-card">
          <span>BLOCKED</span>
          <strong>{blocked}</strong>
        </div>
      </div>
    </section>
  );
}
