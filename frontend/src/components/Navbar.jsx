import { shortAddress } from "../lib/format.js";

export default function Navbar({
  backendOnline,
  walletAddress,
  walletBusy,
  onToggleWallet
}) {
  return (
    <header className="navbar">
      <div className="brand">
        <div className="brand-mark">🛡</div>
        <div>
          <div className="brand-name">AGENTSHIELD</div>
          <div className="brand-subtitle">TRUST INFRASTRUCTURE</div>
        </div>
      </div>

      <div className="system-indicator">
        <button
          className={`wallet-btn${walletAddress ? " connected" : ""}`}
          type="button"
          disabled={walletBusy}
          onClick={onToggleWallet}
        >
          {walletBusy
            ? "Connecting..."
            : walletAddress
              ? shortAddress(walletAddress)
              : "Connect Pera"}
        </button>
        <span
          className={`status-dot ${backendOnline ? "online" : "offline"}`}
        ></span>
        <span>{backendOnline ? "SYSTEM ONLINE" : "SYSTEM OFFLINE"}</span>
      </div>
    </header>
  );
}
