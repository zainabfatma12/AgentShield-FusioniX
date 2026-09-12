import { useCallback, useEffect, useRef, useState } from "react";
import Navbar from "./components/Navbar.jsx";
import Hero from "./components/Hero.jsx";
import StatusGrid from "./components/StatusGrid.jsx";
import AgentConsole from "./components/AgentConsole.jsx";
import ProviderGrid from "./components/ProviderGrid.jsx";
import Architecture from "./components/Architecture.jsx";
import Dashboard from "./components/Dashboard.jsx";
import TransactionList from "./components/TransactionList.jsx";
import TrustModal from "./components/TrustModal.jsx";
import Notification from "./components/Notification.jsx";
import * as api from "./lib/api.js";
import {
  clamp,
  normalizeDecision,
  normalizeProvider,
  numberValue,
  riskFromDecision,
  shortAddress
} from "./lib/format.js";
import {
  connectWallet,
  disconnectWallet,
  onWalletDisconnect,
  reconnectWallet
} from "./lib/wallet.js";

export default function App() {
  const [backendOnline, setBackendOnline] = useState(false);
  const [paymentNetwork, setPaymentNetwork] = useState(null);
  const [providers, setProviders] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [walletAddress, setWalletAddress] = useState(null);
  const [walletBusy, setWalletBusy] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [currentProvider, setCurrentProvider] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [authorization, setAuthorization] = useState(null);
  const [paymentFailed, setPaymentFailed] = useState(false);
  const [authorizing, setAuthorizing] = useState(false);
  const [notice, setNotice] = useState(null);

  const walletSessionRef = useRef(null);
  const noticeTimerRef = useRef(null);

  const notify = useCallback((title, message, type = "info") => {
    console.log(`[AgentShield] ${title}: ${message}`);
    setNotice({ title, message, type });
    clearTimeout(noticeTimerRef.current);
    noticeTimerRef.current = setTimeout(() => setNotice(null), 3500);
  }, []);

  const loadTransactions = useCallback(async () => {
    try {
      const data = await api.getTransactions();
      setTransactions(
        Array.isArray(data.transactions) ? data.transactions : []
      );
    } catch (error) {
      console.warn("Transaction history unavailable:", error);
    }
  }, []);

  const checkBackend = useCallback(async () => {
    try {
      await api.getHealth();
      setBackendOnline(true);
      try {
        setPaymentNetwork(await api.getPaymentStatus());
      } catch {
        setPaymentNetwork(null);
      }
      return true;
    } catch {
      setBackendOnline(false);
      return false;
    }
  }, []);

  const attachSession = useCallback((session) => {
    walletSessionRef.current = session;
    setWalletAddress(session.address);
    sessionStorage.setItem("agentshield.wallet", session.address);
    onWalletDisconnect(() => {
      walletSessionRef.current = null;
      setWalletAddress(null);
      sessionStorage.removeItem("agentshield.wallet");
    });
  }, []);

  const requireWallet = useCallback(async () => {
    if (walletSessionRef.current?.address) {
      return walletSessionRef.current.address;
    }
    const session = await connectWallet(paymentNetwork);
    attachSession(session);
    notify("Wallet connected", shortAddress(session.address), "success");
    return session.address;
  }, [attachSession, notify, paymentNetwork]);

  const handleToggleWallet = useCallback(async () => {
    setWalletBusy(true);
    try {
      if (walletAddress) {
        await disconnectWallet();
        walletSessionRef.current = null;
        setWalletAddress(null);
        sessionStorage.removeItem("agentshield.wallet");
        notify("Wallet disconnected", "Pera session closed.", "info");
        return;
      }
      await requireWallet();
    } catch (error) {
      notify("Wallet connection failed", error.message, "error");
    } finally {
      setWalletBusy(false);
    }
  }, [notify, requireWallet, walletAddress]);

  const analyzeProvider = useCallback(
    async (provider) => {
      const payer = await requireWallet();
      const prepared = await api.preparePayment(payer);
      if (!prepared.unsigned_txns?.length) {
        throw new Error(
          prepared.message ||
            "Could not prepare an x402 payment for this wallet."
        );
      }
      if (!walletSessionRef.current?.signGroup) {
        await requireWallet();
      }
      const paymentGroup = await walletSessionRef.current.signGroup(prepared);
      const result = await api.analyzeProvider({
        reputation: provider.reputation,
        successful_transactions: provider.successful_transactions,
        verified: provider.verified,
        price: provider.price,
        payer,
        payment_group: paymentGroup,
        accepted: prepared.accepted,
        payment_index: prepared.payment_index ?? 1,
        resource: prepared.resource
      });

      if (
        result.analyzed === false ||
        !result.payment ||
        result.payment.success !== true
      ) {
        return {
          ...result,
          analyzed: false,
          payment: result.payment ?? null,
          decision: null,
          trust_score: null
        };
      }

      return {
        ...result,
        analyzed: true,
        trust_score: clamp(result.trust_score),
        risk_level: String(
          result.risk_level ?? riskFromDecision(result.decision)
        ).toUpperCase(),
        decision: normalizeDecision(result.decision),
        reputation: numberValue(result.reputation ?? provider.reputation),
        successful_transactions: numberValue(
          result.successful_transactions ?? provider.successful_transactions
        ),
        verified: Boolean(result.verified ?? provider.verified),
        price: numberValue(result.price ?? provider.price),
        payment_protocol: result.payment_protocol ?? "x402",
        payment: result.payment ?? null
      };
    },
    [requireWallet]
  );

  const authorizeProvider = useCallback(async (provider, currentAnalysis) => {
    const result = await api.authorizeTransaction({
      service: provider.name,
      reputation: numberValue(
        currentAnalysis.reputation ?? provider.reputation
      ),
      reliability: numberValue(provider.reliability),
      successful_transactions: numberValue(
        currentAnalysis.successful_transactions ??
          provider.successful_transactions
      ),
      verified: Boolean(currentAnalysis.verified ?? provider.verified),
      price: numberValue(currentAnalysis.price ?? provider.price),
      amount: numberValue(provider.price),
      payment: currentAnalysis.payment ?? null
    });

    return {
      ...result,
      decision: normalizeDecision(result.decision),
      authorized: Boolean(result.authorized),
      trust_score: numberValue(result.trust_score),
      risk_level: String(
        result.risk_level ?? riskFromDecision(result.decision)
      ).toUpperCase(),
      reason:
        result.reason ??
        "AgentShield authorization policy evaluated the transaction.",
      amount: numberValue(result.amount ?? provider.price),
      payment_protocol: result.payment_protocol ?? "x402",
      payment: result.payment ?? currentAnalysis.payment ?? null
    };
  }, []);

  const closeModal = useCallback(() => {
    setModalOpen(false);
    document.body.classList.remove("modal-open");
  }, []);

  const openModal = useCallback(() => {
    setModalOpen(true);
    document.body.classList.add("modal-open");
  }, []);

  const requireBackend = useCallback(() => {
    if (backendOnline) return true;
    notify(
      "Analysis not found",
      `No AgentShield API at ${api.getApiUrl()}. ` +
        "On Windows start FastAPI, then set VITE_API_URL to that URL " +
        "(not the Vercel site).",
      "error"
    );
    return false;
  }, [backendOnline, notify]);

  const handleAnalyze = useCallback(
    async (provider) => {
      if (!requireBackend()) return;
      setBusyId(provider.id);
      notify(
        "x402 payment",
        "Approve the Algorand transaction in Pera.",
        "info"
      );
      try {
        const result = await analyzeProvider(provider);
        setCurrentProvider(provider);
        setAuthorization(null);
        setAnalysis(result);
        setPaymentFailed(result.analyzed !== true);
        openModal();

        if (result.analyzed !== true) {
          notify(
            "x402 payment required",
            result.payment?.message ??
              "Settlement failed. Score was not calculated.",
            "error"
          );
          return;
        }

        const decision = normalizeDecision(result.decision);
        notify(
          "Trust analysis complete",
          `${provider.name}: ${result.trust_score}/100 — ${decision}`,
          decision === "APPROVE"
            ? "success"
            : decision === "BLOCK"
              ? "error"
              : "warning"
        );
      } catch (error) {
        notify("Analysis failed", error.message, "error");
      } finally {
        setBusyId(null);
      }
    },
    [analyzeProvider, notify, openModal, requireBackend]
  );

  const handleUseService = useCallback(
    async (provider) => {
      if (!requireBackend()) return;
      setBusyId(provider.id);
      notify(
        "x402 payment",
        "Approve the Algorand transaction in Pera.",
        "info"
      );
      try {
        const result = await analyzeProvider(provider);
        setCurrentProvider(provider);
        setAnalysis(result);
        setAuthorization(null);
        setPaymentFailed(result.analyzed !== true);
        openModal();

        if (result.analyzed !== true) {
          notify(
            "x402 payment required",
            result.payment?.message ??
              "Settlement failed. Score was not calculated.",
            "error"
          );
          return;
        }

        const auth = await authorizeProvider(provider, result);
        setAuthorization(auth);
        await loadTransactions();
        const decision = normalizeDecision(auth.decision);
        notify(
          "Authorization evaluated",
          `${provider.name}: ${decision}`,
          decision === "APPROVE"
            ? "success"
            : decision === "BLOCK"
              ? "error"
              : "warning"
        );
      } catch (error) {
        notify("Authorization failed", error.message, "error");
      } finally {
        setBusyId(null);
      }
    },
    [analyzeProvider, authorizeProvider, loadTransactions, notify, openModal, requireBackend]
  );

  const handleAuthorize = useCallback(async () => {
    if (!currentProvider || !analysis || paymentFailed) {
      notify(
        "Trust analysis required",
        "Analyze a provider first.",
        "warning"
      );
      return;
    }
    setAuthorizing(true);
    try {
      const auth = await authorizeProvider(currentProvider, analysis);
      setAuthorization(auth);
      await loadTransactions();
      const decision = normalizeDecision(auth.decision);
      notify(
        "Authorization evaluated",
        `${currentProvider.name}: ${decision}`,
        decision === "APPROVE"
          ? "success"
          : decision === "BLOCK"
            ? "error"
            : "warning"
      );
    } catch (error) {
      notify("Authorization failed", error.message, "error");
    } finally {
      setAuthorizing(false);
    }
  }, [
    analysis,
    authorizeProvider,
    currentProvider,
    loadTransactions,
    notify,
    paymentFailed
  ]);

  const handleLaunch = useCallback(async () => {
    setLaunching(true);
    const online = await checkBackend();
    if (online) {
      try {
        await requireWallet();
      } catch (error) {
        notify("Connect a wallet", error.message, "warning");
      }
      notify(
        "AgentShield online",
        "Trust infrastructure connected. Approve x402 in your wallet to analyze.",
        "success"
      );
      document.getElementById("services")?.scrollIntoView({
        behavior: "smooth"
      });
    } else {
      notify(
        "Backend unavailable",
        "Start the API on VITE_API_URL and try again.",
        "error"
      );
    }
    setTimeout(() => setLaunching(false), 1300);
  }, [checkBackend, notify, requireWallet]);

  useEffect(() => {
    let cancelled = false;

    async function boot() {
      const online = await checkBackend();
      if (cancelled) return;
      try {
        const data = await api.getProviders();
        const raw = Array.isArray(data.providers)
          ? data.providers
          : Array.isArray(data)
            ? data
            : [];
        setProviders(raw.map(normalizeProvider));
      } catch (error) {
        notify("Provider discovery failed", error.message, "error");
      }
      await loadTransactions();

      try {
        const network = online ? await api.getPaymentStatus().catch(() => null) : null;
        const session = await reconnectWallet(network);
        if (!cancelled && session) attachSession(session);
      } catch {
        // No previous Pera session.
      }
    }

    boot();
    return () => {
      cancelled = true;
    };
  }, [attachSession, checkBackend, loadTransactions, notify]);

  useEffect(() => {
    function onKey(event) {
      if (event.key === "Escape") closeModal();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [closeModal]);

  useEffect(() => {
    return () => clearTimeout(noticeTimerRef.current);
  }, []);

  return (
    <>
      <div className="background-grid"></div>
      <div className="glow glow-one"></div>
      <div className="glow glow-two"></div>

      <Navbar
        backendOnline={backendOnline}
        apiUrl={api.getApiUrl()}
        walletAddress={walletAddress}
        walletBusy={walletBusy}
        onToggleWallet={handleToggleWallet}
      />

      <main className="container">
        <Hero launching={launching} onLaunch={handleLaunch} />
        <StatusGrid />
        <AgentConsole />
        <ProviderGrid
          providers={providers}
          busyId={busyId}
          onAnalyze={handleAnalyze}
          onUseService={handleUseService}
        />
        <Architecture />
        <Dashboard transactions={transactions} />
        <TransactionList
          transactions={transactions}
          onRefresh={loadTransactions}
        />
      </main>

      <TrustModal
        open={modalOpen}
        provider={currentProvider}
        analysis={analysis}
        authorization={authorization}
        paymentFailed={paymentFailed}
        authorizing={authorizing}
        onClose={closeModal}
        onAuthorize={handleAuthorize}
      />

      <Notification notice={notice} />
    </>
  );
}
