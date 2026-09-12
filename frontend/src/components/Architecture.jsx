export default function Architecture() {
  return (
    <section className="architecture section" id="architecture">
      <div className="section-heading">
        <div>
          <div className="eyebrow">SECURITY ARCHITECTURE</div>
          <h2>Trust → Authorization → Payment</h2>
        </div>
      </div>

      <div className="architecture-flow">
        <div className="architecture-node">
          <div className="node-number">01</div>
          <div className="node-icon">◇</div>
          <h3>AI Agent</h3>
          <p>Discovers and requests services autonomously.</p>
        </div>
        <div className="architecture-arrow">↓</div>
        <div className="architecture-node highlight">
          <div className="node-number">02</div>
          <div className="node-icon">🛡</div>
          <h3>Trust Engine</h3>
          <p>Calculates provider trust and risk.</p>
        </div>
        <div className="architecture-arrow">↓</div>
        <div className="architecture-node highlight">
          <div className="node-number">03</div>
          <div className="node-icon">◉</div>
          <h3>Authorization Gate</h3>
          <p>Decides whether this transaction is permitted.</p>
        </div>
        <div className="architecture-arrow">↓</div>
        <div className="architecture-node payment-node">
          <div className="node-number">04</div>
          <div className="node-icon">$</div>
          <h3>x402 Payment</h3>
          <p>Executes payment only after approval.</p>
        </div>
      </div>

      <div className="architecture-rule">
        <span>SECURITY RULE</span>
        <strong>ANALYZE → x402 SETTLES FIRST</strong>
        <span className="separator">|</span>
        <strong>THEN TRUST SCORE</strong>
      </div>
    </section>
  );
}
