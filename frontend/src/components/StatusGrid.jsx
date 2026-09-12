const CARDS = [
  {
    icon: "◈",
    title: "Trust Engine",
    value: "ONLINE",
    description: "Provider risk evaluation",
    pending: false
  },
  {
    icon: "◉",
    title: "Authorization",
    value: "ACTIVE",
    description: "Transaction policy gate",
    pending: false
  },
  {
    icon: "$",
    title: "x402 Gateway",
    value: "READY",
    description: "Payment protocol",
    pending: true
  },
  {
    icon: "◫",
    title: "Audit Ledger",
    value: "ACTIVE",
    description: "Transaction records",
    pending: false
  }
];

export default function StatusGrid() {
  return (
    <section className="section">
      <div className="section-heading">
        <div>
          <div className="eyebrow">SECURITY CONTROL CENTER</div>
          <h2>Agent Security Status</h2>
        </div>
        <div className="live-badge">
          <span></span>
          LIVE
        </div>
      </div>

      <div className="status-grid">
        {CARDS.map((card) => (
          <div className="status-card" key={card.title}>
            <div className="status-card-top">
              <span className="status-icon">{card.icon}</span>
              <span className={`check${card.pending ? " pending" : ""}`}>
                {card.pending ? "◌" : "✓"}
              </span>
            </div>
            <div className="status-title">{card.title}</div>
            <div className="status-value">{card.value}</div>
            <div className="status-description">{card.description}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
