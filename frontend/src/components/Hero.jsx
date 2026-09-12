export default function Hero({ launching, onLaunch }) {
  return (
    <section className="hero">
      <div className="hero-content">
        <div className="eyebrow">AI COMMERCE SECURITY</div>
        <h1>
          Trust Before
          <span>Autonomous Spending.</span>
        </h1>
        <p>
          AgentShield evaluates digital service providers
          and enforces an authorization boundary before
          autonomous AI agents can spend.
        </p>
        <div className="hero-actions">
          <button
            className="btn btn-primary"
            type="button"
            disabled={launching}
            onClick={onLaunch}
          >
            <span>⚡</span>
            {launching ? "Connecting..." : "Launch Agent"}
          </button>
          <a href="#architecture" className="btn btn-secondary">
            View Architecture
            <span>↓</span>
          </a>
        </div>
      </div>

      <div className="hero-visual">
        <div className="orb">
          <div className="orb-ring ring-one"></div>
          <div className="orb-ring ring-two"></div>
          <div className="orb-ring ring-three"></div>
          <div className="shield-core">🛡</div>
        </div>
        <div className="hero-scan">
          <span></span>
          TRUST ENGINE ACTIVE
        </div>
      </div>
    </section>
  );
}
