export default function AgentConsole() {
  return (
    <section className="agent-console">
      <div className="console-header">
        <div>
          <div className="eyebrow">LIVE AGENT CONSOLE</div>
          <h2>Autonomous Service Discovery</h2>
        </div>
        <div className="console-status">● AGENT READY</div>
      </div>

      <div className="agent-request">
        <div className="agent-avatar">AI</div>
        <div>
          <div className="agent-label">USER REQUEST</div>
          <div className="agent-text">
            "Find me a reliable weather API
            under my spending limit."
          </div>
        </div>
      </div>

      <div className="flow-line">
        <div className="flow-step active">
          <span>01</span>
          DISCOVER
        </div>
        <div className="flow-arrow">→</div>
        <div className="flow-step active">
          <span>02</span>
          EVALUATE
        </div>
        <div className="flow-arrow">→</div>
        <div className="flow-step">
          <span>03</span>
          AUTHORIZE
        </div>
        <div className="flow-arrow">→</div>
        <div className="flow-step">
          <span>04</span>
          PAY
        </div>
      </div>
    </section>
  );
}
