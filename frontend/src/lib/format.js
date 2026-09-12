export function numberValue(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

export function clamp(value, min = 0, max = 100) {
  return Math.max(min, Math.min(max, numberValue(value)));
}

export function shortAddress(address) {
  if (!address) return "";
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

export function normalizeDecision(value) {
  const decision = String(value ?? "REVIEW").toUpperCase().trim();
  if (decision === "APPROVED") return "APPROVE";
  if (decision === "BLOCKED") return "BLOCK";
  return decision;
}

export function riskFromDecision(decision) {
  const normalized = normalizeDecision(decision);
  if (normalized === "APPROVE") return "LOW";
  if (normalized === "REVIEW") return "MEDIUM";
  if (normalized === "BLOCK") return "HIGH";
  return "UNKNOWN";
}

export function priceFairness(price) {
  if (price <= 0.001) return 100;
  if (price <= 0.005) return 75;
  if (price <= 0.01) return 50;
  return 25;
}

export function normalizeProvider(raw, index) {
  return {
    id: raw.id ?? `provider-${index + 1}`,
    name: raw.name ?? raw.service ?? `Provider ${index + 1}`,
    description: raw.description ?? "Digital service provider.",
    reputation: numberValue(raw.reputation),
    reliability: numberValue(raw.reliability),
    successful_transactions: numberValue(raw.successful_transactions),
    verified: Boolean(raw.verified),
    price: numberValue(raw.price),
    payment_protocol: raw.payment_protocol ?? "x402"
  };
}

export function explorerFor(transaction) {
  if (!transaction?.blockchain_tx_id) return null;
  const chain = String(transaction.blockchain ?? "").toLowerCase();
  const net = chain.includes("mainnet") ? "mainnet" : "testnet";
  return `https://lora.algokit.io/${net}/transaction/${encodeURIComponent(
    transaction.blockchain_tx_id
  )}`;
}
