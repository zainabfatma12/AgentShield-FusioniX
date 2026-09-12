import { PeraWalletConnect } from "@perawallet/connect";
import algosdk from "algosdk";

function bytesFromBase64(value) {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

function base64FromBytes(bytes) {
  let binary = "";
  const view = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  for (let i = 0; i < view.length; i += 1) {
    binary += String.fromCharCode(view[i]);
  }
  return btoa(binary);
}

function chainIdForNetwork(networkId) {
  return networkId === "mainnet" ? 416001 : 416002;
}

let peraWallet = null;

function getPera(networkId) {
  if (!peraWallet) {
    peraWallet = new PeraWalletConnect({
      chainId: chainIdForNetwork(networkId),
      shouldShowSignTxnToast: true,
      compactMode: true
    });
  }
  return peraWallet;
}

function getInjectedProvider() {
  if (window.algorand && typeof window.algorand.enable === "function") {
    return window.algorand;
  }
  if (window.exodus?.algorand) {
    return window.exodus.algorand;
  }
  return null;
}

async function signWithInjected(provider, prepared) {
  const unsigned = prepared.unsigned_txns || [];
  const indexes = prepared.indexes_to_sign || [1];
  const txns = unsigned.map((txn, index) => (
    indexes.includes(index) ? { txn } : { txn, signers: [] }
  ));
  const signed = await provider.signTxns(txns);
  return unsigned.map((unsignedTxn, index) => {
    const value = signed?.[index];
    if (!value) return unsignedTxn;
    if (typeof value === "string") return value;
    return value.stxn || value.blob || value.txn || unsignedTxn;
  });
}

async function signWithPera(wallet, prepared) {
  const unsigned = prepared.unsigned_txns || [];
  const indexes = prepared.indexes_to_sign || [1];
  const group = unsigned.map((txn, index) => ({
    txn: algosdk.decodeUnsignedTransaction(bytesFromBase64(txn)),
    signers: indexes.includes(index) ? undefined : []
  }));
  const signedBlobs = await wallet.signTransaction([group]);
  return unsigned.map((unsignedTxn, index) => {
    if (!indexes.includes(index)) return unsignedTxn;
    const blob = Array.isArray(signedBlobs)
      ? (signedBlobs[index] || signedBlobs.find(Boolean))
      : signedBlobs;
    if (!blob) {
      throw new Error("Pera did not return a signed payment transaction.");
    }
    return base64FromBytes(blob);
  });
}

async function connectInjected(network) {
  const provider = getInjectedProvider();
  if (!provider) return null;

  const result = await provider.enable({
    genesisID: network?.genesis_id,
    genesisHash: network?.genesis_hash
  });
  const accounts = result?.accounts ?? result ?? [];
  const address = Array.isArray(accounts) ? accounts[0] : accounts?.address;
  if (!address) return null;

  return {
    address,
    provider: "injected",
    signGroup: (prepared) => signWithInjected(provider, prepared)
  };
}

export async function connectWallet(network) {
  const injected = await connectInjected(network).catch(() => null);
  if (injected) return injected;

  const wallet = getPera(network?.network_id);
  const accounts = await wallet.connect();
  const address = accounts?.[0];
  if (!address) {
    throw new Error("Pera connected but no account was returned.");
  }
  return {
    address,
    provider: "pera",
    signGroup: (prepared) => signWithPera(wallet, prepared)
  };
}

export async function reconnectWallet(network) {
  try {
    const wallet = getPera(network?.network_id);
    const accounts = await wallet.reconnectSession();
    if (wallet.isConnected && accounts?.length) {
      return {
        address: accounts[0],
        provider: "pera",
        signGroup: (prepared) => signWithPera(wallet, prepared)
      };
    }
  } catch {
    // No previous Pera session.
  }
  return null;
}

export async function disconnectWallet() {
  try {
    await peraWallet?.disconnect();
  } catch {
    // Already closed.
  }
}

export function onWalletDisconnect(handler) {
  if (!peraWallet?.connector) return () => {};
  peraWallet.connector.on("disconnect", handler);
  return () => peraWallet.connector?.off?.("disconnect", handler);
}
