import {
  clamp,
  normalizeDecision,
  numberValue,
  priceFairness,
  riskFromDecision
} from "../lib/format.js";

function SettlementPanel({ payment }) {
  if (!payment) return null;

  if (payment.success === true || payment.status === "SETTLED") {
    return (
      <div className="settlement-panel settled">
        <strong>x402 SETTLED ON ALGORAND</strong>
        <div className="auth-details">
          <span>
            Facilitator: <strong>GoPlausible</strong>
          </span>
          <span>
            Network: <strong>{payment.network ?? "Algorand Testnet"}</strong>
          </span>
        </div>
        <p>{payment.message ?? "Payment settled on-chain."}</p>
        <div className="txid">
          TX: <code>{payment.transaction_id ?? "pending"}</code>
          {payment.explorer_url ? (
            <a href={payment.explorer_url} target="_blank" rel="noopener noreferrer">
              View on Algorand
            </a>
          ) : null}
        </div>
        {payment.resource ? (
          <pre className="paid-result">
            {JSON.stringify(payment.resource, null, 2)}
          </pre>
        ) : null}
      </div>
    );
  }

  if (payment.status === "SKIPPED" || payment.status === "NOT_REQUESTED") {
    return (
      <div className="settlement-panel skipped">
        <strong>x402 NOT SENT</strong>
        <p>{payment.message ?? "Payment was not attempted."}</p>
      </div>
    );
  }

  return (
    <div className="settlement-panel failed">
      <strong>x402 SETTLEMENT {payment.status ?? "FAILED"}</strong>
      <p>
        {payment.message ??
          "The facilitator could not settle this payment."}
      </p>
    </div>
  );
}

function AuthorizationResult({ analysis, authorization, paymentFailed }) {
  if (paymentFailed) {
    return <SettlementPanel payment={analysis?.payment} />;
  }

  const result = authorization ?? analysis;
  if (!result) {
    return (
      <div className="authorization-placeholder">
        Analyze a provider to evaluate transaction authorization.
      </div>
    );
  }

  const decision = normalizeDecision(result.decision);
  const score = numberValue(result.trust_score);
  const reason =
    result.reason ?? "AgentShield authorization policy evaluated the transaction.";

  if (decision === "APPROVE") {
    return (
      <div className="authorization-success">
        <div className="auth-icon">✓</div>
        <strong>TRANSACTION AUTHORIZED</strong>
        <div className="auth-details">
          <span>
            Trust: <strong>{score}/100</strong>
          </span>
          <span>
            Decision: <strong>APPROVE</strong>
          </span>
          <span>
            Amount: <strong>${numberValue(result.amount ?? result.price).toFixed(3)}</strong>
          </span>
        </div>
        <p>{reason}</p>
        <div className="payment-ready">
          🛡 Authorization passed. x402 already settled on Algorand.
        </div>
        <SettlementPanel payment={result.payment} />
      </div>
    );
  }

  if (decision === "REVIEW") {
    return (
      <div className="authorization-review">
        <div className="auth-icon">!</div>
        <strong>TRANSACTION PAUSED</strong>
        <div className="auth-details">
          <span>
            Trust: <strong>{score}/100</strong>
          </span>
          <span>
            Decision: <strong>REVIEW</strong>
          </span>
        </div>
        <p>{reason}</p>
        <div>
          x402 payment has <strong>NOT</strong> been authorized.
        </div>
        <SettlementPanel payment={result.payment} />
      </div>
    );
  }

  return (
    <div className="authorization-blocked">
      <div className="auth-icon">×</div>
      <strong>TRANSACTION BLOCKED</strong>
      <div className="auth-details">
        <span>
          Trust: <strong>{score}/100</strong>
        </span>
        <span>
          Decision: <strong>BLOCK</strong>
        </span>
      </div>
      <p>{reason}</p>
      <div>🛡 Payment prevented by AgentShield. x402 was not called.</div>
      <SettlementPanel payment={result.payment} />
    </div>
  );
}

function paymentButtonState(analysis, authorization, paymentFailed, authorizing) {
  if (authorizing) {
    return {
      disabled: true,
      className: "payment-button",
      label: "🛡 Re-checking Authorization..."
    };
  }

  if (paymentFailed || !analysis) {
    return {
      disabled: true,
      className: "payment-button",
      label: paymentFailed ? "Payment Required" : "Analyze Provider First"
    };
  }

  const decision = normalizeDecision((authorization ?? analysis).decision);
  if (decision === "APPROVE") {
    return {
      disabled: Boolean(authorization),
      className: "payment-button payment-approved",
      label: authorization
        ? "✓ Authorization Recorded"
        : "⚡ Proceed with x402 Payment"
    };
  }
  if (decision === "REVIEW") {
    return {
      disabled: true,
      className: "payment-button payment-review",
      label: "⚠ Authorization Required"
    };
  }
  return {
    disabled: true,
    className: "payment-button payment-blocked",
    label: "✕ Payment Blocked"
  };
}

export default function TrustModal({
  open,
  provider,
  analysis,
  authorization,
  paymentFailed,
  authorizing,
  onClose,
  onAuthorize
}) {
  if (!open) return null;

  const name = provider?.name ?? "Service Provider";
  const decision = analysis ? normalizeDecision(analysis.decision) : null;
  const risk = analysis
    ? String(analysis.risk_level ?? riskFromDecision(decision)).toUpperCase()
    : null;
  const reputation = numberValue(analysis?.reputation);
  const verified = Boolean(analysis?.verified);
  const price = numberValue(analysis?.price);
  const history = numberValue(analysis?.successful_transactions);
  const button = paymentButtonState(
    analysis,
    authorization,
    paymentFailed,
    authorizing
  );

  let riskClass = "risk-badge";
  if (risk === "LOW") riskClass += " risk-low";
  else if (risk === "MEDIUM") riskClass += " risk-medium";
  else if (risk === "HIGH") riskClass += " risk-high";

  let decisionClass = "decision-value";
  if (decision === "APPROVE") decisionClass += " approved";
  else if (decision === "REVIEW") decisionClass += " review";
  else if (decision) decisionClass += " blocked";

  return (
    <div
      className="modal active"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="modal-card">
        <button
          className="modal-close"
          type="button"
          aria-label="Close"
          onClick={onClose}
        >
          ×
        </button>

        <div className="modal-header">
          <div className="eyebrow">AGENTSHIELD SECURITY ANALYSIS</div>
          <h2>Trust Analysis</h2>
          <p>{name}</p>
        </div>

        <div className="score-panel">
          <div className="score-number">
            {paymentFailed || !analysis ? "—" : analysis.trust_score}
          </div>
          <div className="score-denominator">/100</div>
          <div className={riskClass}>
            {paymentFailed
              ? "PAYMENT REQUIRED"
              : risk
                ? `${risk} RISK`
                : "ANALYZING"}
          </div>
        </div>

        <div className="analysis-factors">
          <div className="factor">
            <div className="factor-header">
              <span>Reputation</span>
              <strong>
                {analysis && !paymentFailed ? `${Math.round(reputation)}%` : "—"}
              </strong>
            </div>
            <div className="factor-track">
              <div
                className="factor-fill"
                style={{ width: `${clamp(analysis && !paymentFailed ? reputation : 0)}%` }}
              ></div>
            </div>
          </div>

          <div className="factor">
            <div className="factor-header">
              <span>Verification</span>
              <strong>
                {analysis && !paymentFailed
                  ? verified
                    ? "VERIFIED"
                    : "UNVERIFIED"
                  : "—"}
              </strong>
            </div>
            <div className="factor-track">
              <div
                className="factor-fill"
                style={{
                  width: `${analysis && !paymentFailed && verified ? 100 : 0}%`
                }}
              ></div>
            </div>
          </div>

          <div className="factor">
            <div className="factor-header">
              <span>Price</span>
              <strong>
                {analysis && !paymentFailed ? `$${price.toFixed(3)}` : "—"}
              </strong>
            </div>
            <div className="factor-track">
              <div
                className="factor-fill"
                style={{
                  width: `${clamp(analysis && !paymentFailed ? priceFairness(price) : 0)}%`
                }}
              ></div>
            </div>
          </div>

          <div className="factor">
            <div className="factor-header">
              <span>Transaction History</span>
              <strong>
                {analysis && !paymentFailed ? history : "—"}
              </strong>
            </div>
            <div className="factor-track">
              <div
                className="factor-fill"
                style={{
                  width: `${clamp(analysis && !paymentFailed ? Math.min(100, history / 2) : 0)}%`
                }}
              ></div>
            </div>
          </div>
        </div>

        <div className="decision-panel">
          <div className="decision-label">AGENT DECISION</div>
          <div className={decisionClass}>
            {paymentFailed || !decision ? "—" : decision}
          </div>
          <div className="protocol-badge">
            <span>{analysis?.payment_protocol ?? "x402"}</span>
          </div>
        </div>

        <div className="authorization-result">
          <AuthorizationResult
            analysis={analysis}
            authorization={authorization}
            paymentFailed={paymentFailed}
          />
        </div>

        <button
          className={button.className}
          type="button"
          disabled={button.disabled}
          onClick={onAuthorize}
        >
          {button.label}
        </button>

        <div className="payment-note">
          Connect Pera (QR or extension). Analyze asks the wallet to sign x402,
          settles on-chain, then shows the score.
        </div>
      </div>
    </div>
  );
}
