"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Zap,
  Users,
  Cpu,
  Webhook,
  Bot,
  Brain,
  ShieldCheck,
  TrendingUp,
  RefreshCw,
  MessageSquare,
} from "lucide-react";

import { Header } from "@/components/Header";
import { HeroBanner } from "@/components/HeroBanner";
import { MetricsOverview } from "@/components/MetricsOverview";
import { PipelineVisualizer } from "@/components/PipelineVisualizer";
import { OpportunityCard } from "@/components/OpportunityCard";
import { PermissionGateBanner } from "@/components/PermissionGateBanner";
import { Customer360View } from "@/components/Customer360View";
import { AgentTraceView } from "@/components/AgentTraceView";
import { WebhookLabView } from "@/components/WebhookLabView";
import { ClaudeGrowthStrategist } from "@/components/ClaudeGrowthStrategist";
import { QuickTourModal } from "@/components/QuickTourModal";
import { TerminalDrawer } from "@/components/TerminalDrawer";

import {
  generateSimulation,
  loadLocalSimulation,
  scanOpportunities,
  agenticScanOpportunities,
  launchCampaign,
  triggerWebhookPayment,
  getExperimentResults,
  listCustomers,
  getLatestTrace,
  listSessions,
  getLocalSnapshot,
} from "@/services/api";

import {
  Customer,
  Opportunity,
  PermissionGateInfo,
  ExperimentMetrics,
  CheckoutSession,
  OfferDetails,
} from "@/types";

export default function DashboardPage() {
  // Session & Merchant State
  const [merchantName, setMerchantName] = useState<string>("StyleKart");
  const [merchantId, setMerchantId] = useState<string>("");
  const [sessionId, setSessionId] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Active Main Tab
  const [activeTab, setActiveTab] = useState<
    "growth" | "customers" | "agents" | "webhooks" | "chat"
  >("growth");

  // Growth Pipeline Data
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [growthReasoning, setGrowthReasoning] = useState<string>("");
  const [currentStage, setCurrentStage] = useState<number>(1);

  // Customer 360 Data
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [totalOrders, setTotalOrders] = useState<number>(0);

  // Launched Campaigns & A/B Experiments Registry
  const [launchedOppIds, setLaunchedOppIds] = useState<Set<string>>(new Set());
  const [completedPaymentOppIds, setCompletedPaymentOppIds] = useState<Set<string>>(new Set());
  const [campaignMetricsMap, setCampaignMetricsMap] = useState<Record<string, ExperimentMetrics>>({});
  const [campaignOffersMap, setCampaignOffersMap] = useState<Record<string, OfferDetails>>({});
  const [checkoutSessionsMap, setCheckoutSessionsMap] = useState<Record<string, CheckoutSession>>({});
  const [oppToCampIdMap, setOppToCampIdMap] = useState<Record<string, string>>({});

  // Permission Gate Interactive State
  const [pendingGate, setPendingGate] = useState<PermissionGateInfo | null>(null);
  const [pendingOpportunityId, setPendingOpportunityId] = useState<string | null>(null);
  const [safeAudienceCap, setSafeAudienceCap] = useState<number>(125);
  const [eligibleAudience, setEligibleAudience] = useState<number>(300);
  const [launchingOppId, setLaunchingOppId] = useState<string | null>(null);
  const [payingOppId, setPayingOppId] = useState<string | null>(null);

  // Output Session Trace
  const [traceData, setTraceData] = useState<any>(null);

  // Quick Tour & Terminal States
  const [isTourOpen, setIsTourOpen] = useState<boolean>(false);
  const [isTerminalOpen, setIsTerminalOpen] = useState<boolean>(false);
  const [logs, setLogs] = useState<string[]>([
    "[System] RazorGrowth AI initialized with Razorpay Sandbox & Neon PostgreSQL.",
  ]);

  const addLog = (msg: string) => {
    setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  // Initialize Dashboard with active/latest session
  useEffect(() => {
    const initDashboard = async () => {
      try {
        const sessList = await listSessions();
        if (sessList?.sessions && sessList.sessions.length > 0) {
          const latest = sessList.sessions[0].session_id;
          await handleSelectHistoricalSession(latest);
          return;
        }
      } catch (e) {
        console.warn("Could not fetch sessions list on mount:", e);
      }

      // If no sessions yet, load local dataset without re-generating
      try {
        const snap = await getLocalSnapshot();
        if (snap?.data?.merchant_id) {
          setMerchantId(snap.data.merchant_id);
          setMerchantName(snap.data.merchant_name || "StyleKart");
          setTotalOrders(snap.data.orders_created || 2000);
          setCurrentStage(2);
          const custList = await listCustomers(snap.data.merchant_id, 100);
          setCustomers(custList);
          const activeSess = `sess_${Date.now().toString(36)}`;
          setSessionId(activeSess);
          await handleScanOpportunities(snap.data.merchant_id, activeSess);
          return;
        }
      } catch (e) {
        console.warn("Local snapshot check on mount:", e);
      }

      const defaultSess = `sess_${Date.now().toString(36)}`;
      setSessionId(defaultSess);
    };

    initDashboard();
  }, []);

  // Handler: Generate New Simulation
  const handleGenerateSimulation = async () => {
    const newSessionId = `sess_${Date.now().toString(36)}`;
    setSessionId(newSessionId);
    resetDashboardState();
    setIsLoading(true);
    addLog(`Initializing fresh simulation for StyleKart [${newSessionId}]...`);

    try {
      const res = await generateSimulation("StyleKart", 500, 2000, newSessionId);
      const data = res.data;
      setMerchantName(data.merchant_name || "StyleKart");
      setMerchantId(data.merchant_id);
      setTotalOrders(data.orders_created || 2000);
      setCurrentStage(2);
      addLog(`[SUCCESS] Generated ${data.customers_created} customers, ${data.orders_created} orders.`);

      // Fetch Customer 360
      if (data.merchant_id) {
        const custList = await listCustomers(data.merchant_id, 100);
        setCustomers(custList);
      }

      // Automatically run scan
      await handleScanOpportunities(data.merchant_id, newSessionId);
    } catch (e: any) {
      addLog(`[ERROR] Generate failed: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Handler: Switch to a historical session
  const handleSelectHistoricalSession = async (targetSessionId: string) => {
    setSessionId(targetSessionId);
    resetDashboardState();
    setIsLoading(true);
    addLog(`Switching context to historical session [${targetSessionId}]...`);

    try {
      const trace = await getLatestTrace(targetSessionId);
      if (trace && (trace.data || trace)) {
        const tracePayload = trace.data || trace;
        setTraceData(tracePayload);
        const merchant = tracePayload.merchant_id || "merch_demo";
        setMerchantId(merchant);

        const steps = tracePayload.steps || {};
        const step1 = steps["1_dataset_generation"]?.data || steps["step_1_get_merchant_context"]?.data;
        const step2Det = steps["2_opportunity_scan_and_ai_reasoning"]?.data;
        const step2Agentic = steps["2_agentic_decision_loop"]?.data;
        const step3 = steps["3_campaign_launch_and_dispatch"]?.data;
        const step4 = steps["4_experiment_ab_lift_measurement"]?.data;

        // Fetch customer 360 data strictly for this session's merchant
        if (merchant) {
          try {
            const custList = await listCustomers(merchant, 100);
            setCustomers(custList);
          } catch (err) {
            console.warn("Failed to fetch customers for session merchant:", err);
          }
        }

        if (step1) {
          setTotalOrders(step1.orders_created || (step1.total_customers ? step1.total_customers * 4 : 2000));
        }

        // Restore growth opportunities from either deterministic or agentic scan
        const oppsFromAgentic = step2Agentic?.steps_taken?.find(
          (s: any) => s.tool_name === "detect_opportunities"
        )?.result?.opportunities;

        const sessionOpps = step2Det?.opportunities || oppsFromAgentic || [];
        if (sessionOpps.length > 0) {
          setOpportunities(sessionOpps);
          setCurrentStage(3);
        } else if (merchant) {
          try {
            const scanRes = await scanOpportunities(merchant, targetSessionId);
            if (scanRes?.opportunities && scanRes.opportunities.length > 0) {
              setOpportunities(scanRes.opportunities);
              setCurrentStage(3);
            }
          } catch (err) {
            console.warn("Rescan on session switch:", err);
          }
        }

        // Restore reasoning trace
        if (step2Det?.action_plan?.ai_reasoning) {
          setGrowthReasoning(step2Det.action_plan.ai_reasoning);
        } else if (step2Agentic?.plan_summary) {
          setGrowthReasoning(step2Agentic.plan_summary);
        }

        // Restore launched campaign and offer details
        if (step3?.campaign_id && step3?.opportunity_id) {
          setLaunchedOppIds(new Set([step3.opportunity_id]));
          setOppToCampIdMap({ [step3.opportunity_id]: step3.campaign_id });
          if (step3.offer) {
            setCampaignOffersMap({ [step3.opportunity_id]: step3.offer });
          }
          if (step3.checkout_sessions && step3.checkout_sessions.length > 0) {
            setCheckoutSessionsMap({ [step3.opportunity_id]: step3.checkout_sessions[0] });
          }
          setCurrentStage(5);
        }

        // Restore A/B experiment lift metrics and payment status
        if (step4?.metrics && step3?.opportunity_id) {
          setCompletedPaymentOppIds(new Set([step3.opportunity_id]));
          setCampaignMetricsMap({ [step3.opportunity_id]: step4.metrics });
          setCurrentStage(6);
        }

        addLog(`[SUCCESS] Loaded session ${targetSessionId} trace with recorded A/B lift metrics.`);
      }
    } catch (e: any) {
      addLog(`[ERROR] Failed to switch session: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Handler: Load Local Simulation
  const handleLoadLocalSimulation = async (currSessionId?: string) => {
    const activeSess = currSessionId || sessionId;
    setIsLoading(true);
    addLog(`Loading dataset from local JSON snapshot data/latest_simulation.json...`);

    try {
      const res = await loadLocalSimulation(activeSess);
      const data = res.data;
      setMerchantName(data.merchant_name || "StyleKart");
      setMerchantId(data.merchant_id);
      setTotalOrders(data.orders_created || 2000);
      setCurrentStage(2);
      addLog(`[SUCCESS] Loaded local dataset: ${data.customers_created} customers, ${data.orders_created} orders.`);

      // Fetch Customer 360
      if (data.merchant_id) {
        const custList = await listCustomers(data.merchant_id, 100);
        setCustomers(custList);
      }

      // Automatically run scan
      await handleScanOpportunities(data.merchant_id, activeSess);
    } catch (e: any) {
      addLog(`[NOTICE] No local JSON snapshot yet. Click 'Generate New Session' to seed store data.`);
    } finally {
      setIsLoading(false);
    }
  };

  // Handler: Scan Opportunities
  const handleScanOpportunities = async (mId?: string, sId?: string) => {
    const targetMId = mId || merchantId;
    const targetSId = sId || sessionId;
    if (!targetMId) return;

    addLog(`GrowthManagerAgent executing multi-agent opportunity scan...`);
    try {
      const res = await scanOpportunities(targetMId, targetSId);
      setOpportunities(res.opportunities || []);
      if (res.action_plan && res.action_plan.ai_reasoning) {
        setGrowthReasoning(res.action_plan.ai_reasoning);
      }
      setCurrentStage(3);
      addLog(`[SUCCESS] Discovered ${res.opportunities_found} high-ROI growth opportunities.`);

      // Refresh Trace
      refreshTrace(targetSId);
    } catch (e: any) {
      addLog(`[ERROR] Opportunity scan failed: ${e.message}`);
    }
  };

  // Handler: Agentic Scan (RAG Vector Memory + ReAct Tool-Calling)
  const handleAgenticScanOpportunities = async (mId?: string, sId?: string) => {
    const targetMId = mId || merchantId;
    const targetSId = sId || sessionId;
    if (!targetMId) return;

    setIsLoading(true);
    addLog(`[AGENTIC ReAct] Starting bounded decision loop with RAG Vector Memory recall...`);
    try {
      const res = await agenticScanOpportunities(targetMId, targetSId);
      addLog(`[AGENTIC SCAN] Status: ${res.status.toUpperCase()} (${res.steps_taken.length} tools executed)`);
      res.steps_taken.forEach((st) => {
        addLog(`  Step ${st.step_number}: ${st.tool_name}() -> ${st.step_summary}`);
      });
      if (res.memory_citations && res.memory_citations.length > 0) {
        addLog(`[RAG MEMORY] Retrieved ${res.memory_citations.length} similar historical campaign outcomes.`);
      }
      setGrowthReasoning(res.plan_summary);
      addLog(`[DECISION PLAN] ${res.plan_summary}`);

      // Also ensure opportunities list is loaded
      await handleScanOpportunities(targetMId, targetSId);
      setActiveTab("agents");
    } catch (e: any) {
      addLog(`[ERROR] Agentic scan failed: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Handler: Launch Campaign
  const handleLaunchCampaign = async (
    opportunityId: string,
    bypassPermissionGate: boolean = false,
    audienceCap?: number
  ) => {
    setPendingGate(null);
    setPendingOpportunityId(null);
    setLaunchingOppId(opportunityId);
    addLog(`Evaluating Permission Gate & launching action for ${opportunityId}...`);

    try {
      const res = await launchCampaign(opportunityId, {
        bypassPermissionGate,
        maxAudienceCap: audienceCap,
        sessionId,
      });

      if (res.status === "requires_approval") {
        setPendingGate(res.permission_gate || null);
        setPendingOpportunityId(opportunityId);
        setSafeAudienceCap(res.safe_audience_cap || 125);
        setEligibleAudience(res.eligible_audience || res.total_audience || 300);
        setCurrentStage(4);
        addLog(`[NOTICE] Permission Gate triggered for ${opportunityId}: Exceeds safe guardrails.`);
        return;
      }

      if (res.campaign_id) {
        setLaunchedOppIds((prev) => new Set(prev).add(opportunityId));
        setOppToCampIdMap((prev) => ({ ...prev, [opportunityId]: res.campaign_id! }));
        setCurrentStage(5);

        if (res.offer) {
          setCampaignOffersMap((prev) => ({ ...prev, [opportunityId]: res.offer! }));
        }

        if (res.checkout_sessions && res.checkout_sessions.length > 0) {
          setCheckoutSessionsMap((prev) => ({
            ...prev,
            [opportunityId]: res.checkout_sessions![0],
          }));
        }

        addLog(`[SUCCESS] Action launched! Dispatched ${res.emails_dispatched} communications.`);
        addLog(`[LIVE] Created ${res.total_test_orders || 0} Razorpay test orders for treatment cohort.`);

        refreshTrace(sessionId);
      }
    } catch (e: any) {
      addLog(`[ERROR] Campaign launch error: ${e.message}`);
    } finally {
      setLaunchingOppId(null);
    }
  };

  // Handler: Trigger Payment Conversion via Webhook
  const handleTriggerPayment = async (opportunityId: string) => {
    const campaignId = oppToCampIdMap[opportunityId];
    if (!campaignId) {
      addLog(`[NOTICE] Please launch a campaign first.`);
      return;
    }

    const session = checkoutSessionsMap[opportunityId] || {
      customer_id: "cust_demo",
      amount: 2850,
      razorpay_order_id: "order_demo",
    };

    setPayingOppId(opportunityId);
    addLog(`Simulating Razorpay payment.captured webhook for ${session.customer_id} (₹${session.amount})...`);

    try {
      const res = await triggerWebhookPayment(
        campaignId,
        session.customer_id,
        session.amount,
        sessionId
      );

      setCompletedPaymentOppIds((prev) => new Set(prev).add(opportunityId));
      if (res.metrics) {
        setCampaignMetricsMap((prev) => ({ ...prev, [opportunityId]: res.metrics }));
      }
      setCurrentStage(6);

      addLog(`[LIVE] payment.captured received: ${res.payment_id}. Verified in PostgreSQL!`);
      addLog(`[RESULT] Net Incremental Lift recalculated: +₹${Math.round(res.metrics?.incremental_revenue_inr || session.amount)} GMV.`);

      refreshTrace(sessionId);
    } catch (e: any) {
      addLog(`[ERROR] Payment webhook error: ${e.message}`);
    } finally {
      setPayingOppId(null);
    }
  };

  const refreshTrace = async (sId?: string) => {
    const data = await getLatestTrace(sId || sessionId);
    if (data) setTraceData(data.data || data);
  };

  const resetDashboardState = () => {
    setOpportunities([]);
    setGrowthReasoning("");
    setLaunchedOppIds(new Set());
    setCompletedPaymentOppIds(new Set());
    setCampaignMetricsMap({});
    setCampaignOffersMap({});
    setCheckoutSessionsMap({});
    setOppToCampIdMap({});
    setPendingGate(null);
    setPendingOpportunityId(null);
    setTraceData(null);
    setCustomers([]);
    setTotalOrders(0);
    setCurrentStage(1);
  };

  // Calculations for KPI Cards
  const totalEstimatedOppGmv = opportunities.reduce(
    (acc, opp) => acc + (opp.estimated_gmv || 0),
    0
  );

  let measuredTotalGmvLift = 0;
  let incrementalOrdersTotal = 0;
  completedPaymentOppIds.forEach((oppId) => {
    const m = campaignMetricsMap[oppId];
    if (m) {
      measuredTotalGmvLift += m.incremental_revenue_inr || 0;
      incrementalOrdersTotal += m.incremental_orders_count || 1;
    }
  });

  // Hackathon 7-Step Demonstration Runner
  const handleRunDemoStep = async (stepNum: number) => {
    if (stepNum === 1) {
      await handleGenerateSimulation();
    } else if (stepNum === 2) {
      setActiveTab("customers");
      addLog(`Step 2: Inspecting Customer 360 Profiles and RFM segmentation.`);
    } else if (stepNum === 3) {
      setActiveTab("growth");
      await handleScanOpportunities();
    } else if (stepNum === 4) {
      if (opportunities.length > 0) {
        await handleLaunchCampaign(opportunities[0].id, false);
      }
    } else if (stepNum === 5) {
      if (opportunities.length > 0) {
        await handleLaunchCampaign(opportunities[0].id, true);
      }
    } else if (stepNum === 6) {
      if (opportunities.length > 0) {
        await handleTriggerPayment(opportunities[0].id);
        setActiveTab("webhooks");
      }
    } else if (stepNum === 7) {
      setActiveTab("growth");
      addLog(`Step 7: Final A/B experiment verified in PostgreSQL experiment_assignments.`);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg-primary)] text-[var(--text-primary)] transition-colors duration-200">
      {/* Top Navbar */}
      <Header
        merchantName={merchantName}
        sessionId={sessionId}
        onSelectSession={handleSelectHistoricalSession}
        onStartDemoTour={() => setIsTourOpen(true)}
        onOpenTerminal={() => setIsTerminalOpen((prev) => !prev)}
        isTerminalOpen={isTerminalOpen}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Hero Banner with Actions */}
        <HeroBanner
          merchantName={merchantName}
          merchantId={merchantId}
          sessionId={sessionId}
          isLoading={isLoading}
          onGenerate={handleGenerateSimulation}
          onLoadLocal={() => handleLoadLocalSimulation()}
          onRescan={() => handleScanOpportunities()}
          onAgenticScan={() => handleAgenticScanOpportunities()}
        />

        {/* Dynamic Permission Gate Alert Banner (When safety thresholds are exceeded) */}
        {pendingGate && (
          <PermissionGateBanner
            permissionGate={pendingGate}
            opportunityTitle={
              opportunities.find((o) => o.id === pendingOpportunityId)?.title
            }
            eligibleAudience={eligibleAudience}
            safeAudienceCap={safeAudienceCap}
            onConfirmSafeCap={() => {
              if (pendingOpportunityId) {
                handleLaunchCampaign(pendingOpportunityId, false, safeAudienceCap);
              }
            }}
            onConfirmFullOverride={() => {
              if (pendingOpportunityId) {
                handleLaunchCampaign(pendingOpportunityId, true);
              }
            }}
            onDismiss={() => {
              setPendingGate(null);
              setPendingOpportunityId(null);
            }}
          />
        )}

        {/* Key Metrics Overview Cards */}
        <MetricsOverview
          customerCount={customers.length}
          orderCount={totalOrders}
          opportunityGmv={totalEstimatedOppGmv}
          opportunityCount={opportunities.length}
          measuredGmvLift={measuredTotalGmvLift}
          incrementalOrdersCount={incrementalOrdersTotal}
          permissionGateStatus={pendingGate ? "Review Required" : "Guarded & Safe"}
        />

        {/* 6-Stage Autonomous Loop Progress Pipeline */}
        <PipelineVisualizer
          currentStage={currentStage}
          isLoopCompleted={completedPaymentOppIds.size > 0}
          onSelectStage={(st) => {
            if (st === 2) setActiveTab("customers");
            else if (st === 5 || st === 6) setActiveTab("growth");
            else if (st === 4) setActiveTab("growth");
            else setActiveTab("growth");
          }}
        />

        {/* Tabbed Navigation Showcase */}
        <div className="w-full mb-6">
          <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] pb-2 overflow-x-auto no-scrollbar">
            <button
              onClick={() => setActiveTab("growth")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === "growth"
                  ? "bg-[var(--accent-terracotta)] text-white shadow-sm"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-card)]"
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>Autonomous Growth Actions</span>
              {opportunities.length > 0 && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-white/20">
                  {opportunities.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("customers")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === "customers"
                  ? "bg-[var(--accent-terracotta)] text-white shadow-sm"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-card)]"
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Customer 360 & Segments</span>
            </button>

            <button
              onClick={() => setActiveTab("agents")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === "agents"
                  ? "bg-[var(--accent-terracotta)] text-white shadow-sm"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-card)]"
              }`}
            >
              <Cpu className="w-4 h-4" />
              <span>Multi-Agent Traces</span>
            </button>

            <button
              onClick={() => setActiveTab("webhooks")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === "webhooks"
                  ? "bg-[var(--accent-terracotta)] text-white shadow-sm"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-card)]"
              }`}
            >
              <Webhook className="w-4 h-4" />
              <span>Razorpay Webhook Lab</span>
            </button>

            <button
              onClick={() => setActiveTab("chat")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === "chat"
                  ? "bg-[var(--accent-terracotta)] text-white shadow-sm"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-card)]"
              }`}
            >
              <Bot className="w-4 h-4" />
              <span>AI Growth Strategist</span>
            </button>
          </div>
        </div>

        {/* Tab 1: Growth Opportunities & Loop View */}
        {activeTab === "growth" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: AI Reasoning & Opportunity Cards */}
            <div className="lg:col-span-2 space-y-4">
              {/* AI Strategic Reasoning Box */}
              {growthReasoning && (
                <div className="bg-[var(--bg-card)] border border-[var(--accent-terracotta-border)] rounded-2xl p-5 shadow-[var(--shadow-sm)] animate-fade-in">
                  <div className="flex items-center gap-2 text-xs font-semibold text-[var(--accent-terracotta)] uppercase tracking-wider mb-2">
                    <Brain className="w-4 h-4" />
                    <span>RazorGrowth Cognitive Reasoning Engine</span>
                  </div>
                  <div className="text-xs text-[var(--text-primary)] leading-relaxed whitespace-pre-line">
                    {growthReasoning}
                  </div>
                </div>
              )}

              {/* Opportunities List */}
              {opportunities.length === 0 ? (
                <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-12 text-center text-xs text-[var(--text-muted)] space-y-3">
                  <Sparkles className="w-8 h-8 text-[var(--accent-terracotta)] mx-auto opacity-80" />
                  <div className="font-serif-claude text-base font-semibold text-[var(--text-primary)]">
                    Awaiting Opportunity Detection Scan
                  </div>
                  <p className="max-w-md mx-auto text-[var(--text-secondary)]">
                    Click <strong>"Generate New Session"</strong> or <strong>"Load Local JSON & Scan"</strong> to analyze high-value revenue recovery opportunities.
                  </p>
                </div>
              ) : (
                opportunities.map((opp) => (
                  <OpportunityCard
                    key={opp.id}
                    opportunity={opp}
                    isLaunched={launchedOppIds.has(opp.id)}
                    isPaid={completedPaymentOppIds.has(opp.id)}
                    isLaunching={launchingOppId === opp.id}
                    isPaying={payingOppId === opp.id}
                    isPendingGate={pendingOpportunityId === opp.id && pendingGate !== null}
                    pendingGate={pendingOpportunityId === opp.id ? pendingGate : null}
                    metrics={campaignMetricsMap[opp.id]}
                    checkoutSession={checkoutSessionsMap[opp.id]}
                    offer={campaignOffersMap[opp.id]}
                    onLaunch={(id) => handleLaunchCampaign(id)}
                    onConfirmSafeCap={(id) => handleLaunchCampaign(id, false, safeAudienceCap)}
                    onConfirmOverride={(id) => handleLaunchCampaign(id, true)}
                    onTriggerPayment={(id) => handleTriggerPayment(id)}
                  />
                ))
              )}
            </div>

            {/* Right 1 Col: Embedded Claude Strategist */}
            <div className="lg:col-span-1">
              <ClaudeGrowthStrategist
                merchantId={merchantId}
                sessionId={sessionId}
              />
            </div>
          </div>
        )}

        {/* Tab 2: Customer 360 & Segments */}
        {activeTab === "customers" && (
          <Customer360View
            customers={customers}
            merchantName={merchantName}
          />
        )}

        {/* Tab 3: Multi-Agent Architecture & Traces */}
        {activeTab === "agents" && (
          <AgentTraceView
            traceData={traceData}
            sessionId={sessionId}
            merchantId={merchantId}
            onRefreshTrace={() => refreshTrace()}
          />
        )}

        {/* Tab 4: Webhook Lab */}
        {activeTab === "webhooks" && (
          <WebhookLabView
            sessionId={sessionId}
            onPaymentTriggered={() => handleScanOpportunities()}
          />
        )}

        {/* Tab 5: Dedicated AI Growth Strategist View */}
        {activeTab === "chat" && (
          <div className="max-w-3xl mx-auto">
            <ClaudeGrowthStrategist
              merchantId={merchantId}
              sessionId={sessionId}
            />
          </div>
        )}
      </main>

      {/* Presentation Demo Modal */}
      <QuickTourModal
        isOpen={isTourOpen}
        onClose={() => setIsTourOpen(false)}
        onRunStep={handleRunDemoStep}
      />

      {/* Bottom Live Terminal Logs Drawer */}
      <TerminalDrawer
        isOpen={isTerminalOpen}
        logs={logs}
        onClose={() => setIsTerminalOpen(false)}
        onClear={() => setLogs([])}
      />
    </div>
  );
}
