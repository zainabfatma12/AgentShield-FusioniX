export default function ProviderGrid({
  providers,
  busyId,
  onAnalyze,
  onUseService
}) {
  return (
    <section className="section" id="services">
      <div className="section-heading">
        <div>
          <div className="eyebrow">SERVICE DISCOVERY</div>
          <h2>Providers Evaluated by AgentShield</h2>
        </div>
        <div className="provider-counter">
          <span>{providers.length}</span>
          SERVICES
        </div>
      </div>

      <div className="service-grid">
        {providers.map((provider) => {
          const busy = busyId === provider.id;
          return (
            <article className="service-card" key={provider.id}>
              <div className="service-top">
                <div className="service-icon">☁</div>
                <span
                  className={
                    provider.verified ? "verified" : "verified unverified"
                  }
                >
                  {provider.verified ? "✓ VERIFIED" : "⚠ UNVERIFIED"}
                </span>
              </div>
              <h3>{provider.name}</h3>
              <p>{provider.description}</p>
              <div className="service-stats">
                <div className="service-stat">
                  <span>REPUTATION</span>
                  <strong>{Math.round(provider.reputation)}/100</strong>
                </div>
                <div className="service-stat">
                  <span>TRANSACTIONS</span>
                  <strong>{provider.successful_transactions}</strong>
                </div>
                <div className="service-stat">
                  <span>PRICE</span>
                  <strong>${provider.price.toFixed(3)}</strong>
                </div>
              </div>
              <div className="service-actions">
                <button
                  className="analyze-btn"
                  type="button"
                  disabled={busy}
                  onClick={() => onAnalyze(provider)}
                >
                  {busy ? "Paying..." : "Analyze Trust"}
                </button>
                <button
                  className="use-btn"
                  type="button"
                  disabled={busy}
                  onClick={() => onUseService(provider)}
                >
                  {busy ? "Paying..." : "Use Service"}
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
