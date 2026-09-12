const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(
  /\/$/,
  ""
);

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers
    },
    ...options
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail = data?.detail || data?.message || `HTTP ${response.status}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  return data;
}

export function getApiUrl() {
  return API_URL;
}

export function getHealth() {
  return request("/health");
}

export function getPaymentStatus() {
  return request("/payment/status");
}

export function getProviders() {
  return request("/providers");
}

export function getTransactions() {
  return request("/transactions");
}

export function preparePayment(payer) {
  return request("/payment/prepare", {
    method: "POST",
    body: JSON.stringify({ payer })
  });
}

export function analyzeProvider(payload) {
  return request("/analyze", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function authorizeTransaction(payload) {
  return request("/authorize", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
