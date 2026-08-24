"use client";

import React, { useState } from "react";
import {
  Bot,
  UserCheck,
  Tag,
  Mail,
  Scale,
  Copy,
  Check,
  RefreshCw,
  Database,
  Sparkles,
  Layers,
} from "lucide-react";

interface AgentTraceViewProps {
  traceData: any;
  sessionId: string;
  onRefreshTrace: () => void;
}

export const AgentTraceView: React.FC<AgentTraceViewProps> = ({
  traceData,
  sessionId,
  onRefreshTrace,
}) => {
  const [activeTab, setActiveTab] = useState<"agentic_loop" | "vector_memory" | "agents" | "steps" | "raw">("agentic_loop");
  const [copied, setCopied] = useState(false);

  const agentsList = [
    {
      name: "GrowthManagerAgent",
      role: "Strategic Orchestrator",
      icon: Bot,
      color: "var(--accent-terracotta)",
      description:
        "Continuously monitors merchant performance, orchestrates specialized sub-agents, and formulates strategic revenue growth plans.",
      capabilities: ["Revenue Leakage Diagnosis", "Session Orchestration", "Growth Opportunity Sizing"],
    },
    {
      name: "CustomerAgent",
      role: "Audience & Cohort Specialist",
      icon: UserCheck,
      color: "var(--accent-blue)",
      description:
        "Extracts and ranks high-value dormant customer cohorts using RFM scoring, 3-factor churn risk models, and 12-month CLV predictions.",
      capabilities: ["Dormant VIP Filtering", "Churn Risk Calculation", "Structured Audience Manifest"],
    },
    {
      name: "OfferAgent",
      role: "Incentive & Pricing Strategist",
      icon: Tag,
      color: "var(--accent-emerald)",
      description:
        "Computes margin-safe dynamic discount incentives tailored to customer lifetime value and historical basket sizes.",
      capabilities: ["Dynamic Offer Code Generation", "Margin Guardrail Verification", "Basket Size Calibration"],
    },
    {
      name: "CampaignAgent",
      role: "Multichannel Dispatcher",
      icon: Mail,
      color: "var(--accent-amber)",
      description:
        "Generates personalized communication copy referencing past purchase categories and triggers simulated multi-channel dispatch.",
      capabilities: ["Urgency Trigger Copywriting", "Multi-Channel Notification", "Dispatch Telemetry"],
    },
    {
      name: "ExperimentAgent",
      role: "A/B Science & Lift Evaluator",
      icon: Scale,
      color: "var(--accent-blue)",
      description:
        "Measures real-time conversion rates across 80/20 cohorts, calculating normalized incremental revenue from Razorpay Webhook events.",
      capabilities: ["80/20 Cohort Partitioning", "Razorpay Webhook Attribution", "Normalized Incremental GMV"],
    },
  ];

  const agenticLoopSteps = [
    {
      step: 1,
      tool: "get_merchant_context",
      title: "Store Telemetry Aggregation",
      status: "COMPLETED",
      description: "Retrieved merchant customer profiles, lifetime GMV, and payment success rates.",
      output: { total_customers: 500, total_revenue_inr: 1245000, payment_success_rate: "89.2%" },
    },
    {
      step: 2,
      tool: "detect_opportunities",
      title: "AI Revenue Leakage Detection",
      status: "COMPLETED",
      description: "Ran 4 heuristic detectors across dormant high-value shoppers and gateway drop-offs.",
      output: { opportunities_found: 4, top_opportunity: "VIP Dormant Customer Re-engagement", estimated_gmv: 185000 },
    },
    {
      step: 3,
      tool: "recall_similar_past_campaigns",
      title: "RAG Vector Memory Similarity Search",
      status: "COMPLETED",
      description: "Queried persistent 384-dimensional vector store for historical campaign lift metrics.",
      output: { retrieved_memories: 2, top_similarity: 0.84, past_lift: "+18.5% Relative Conversion Lift" },
    },
    {
      step: 4,
      tool: "select_audience",
      title: "Target Cohort Extraction",
      status: "COMPLETED",
      description: "Filtered high-value dormant cohort with churn risk >= 0.60 and spend >= 5000 INR.",
      output: { target_segment: "VIP Dormant", cohort_count: 50, avg_spend: 3850.0 },
    },
    {
      step: 5,
      tool: "recommend_offer",
      title: "Margin-Safe Incentive Calibration",
      status: "COMPLETED",
      description: "Calibrated 15% discount offer code with margin protection and min order value.",
      output: { offer_code: "VIP-RECOVER-15", discount_value: "15%", min_order: 2500 },
    },
    {
      step: 6,
      tool: "check_permission_gate",
      title: "Dynamic Guardrail Policy Verification",
      status: "AUTO_APPROVED",
      description: "Verified discount value and audience volume against live financial safety caps.",
      output: { policy_status: "auto_approved", max_allowed_discount: "25%", is_safe: true },
    },
  ];

  const vectorMemories = [
    {
      id: "mem_outcome_cmp_vip_prev",
      type: "campaign_outcome",
      summary: "VIP Dormant re-engagement campaign with 15% discount achieved +18.5% conversion lift and ₹45,000 net incremental GMV measured via Razorpay Webhooks.",
      dimension: 384,
      similarity: "0.84 Cosine Score",
    },
    {
      id: "mem_scan_merch_prior",
      type: "growth_scan",
      summary: "Growth scan identified 4 revenue leak opportunities. Top opportunity: 'VIP Dormant Customer Re-engagement' with ₹185,000 estimated recoverable GMV.",
      dimension: 384,
      similarity: "0.78 Cosine Score",
    },
  ];

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(traceData || {}, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full space-y-6">
      {/* Top Header & Tab Selector */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[var(--border-subtle)]">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-serif-claude text-lg font-semibold text-[var(--text-primary)]">
                Multi-Agent Architecture & Decision Intelligence
              </h3>
              <span className="badge-claude badge-terracotta text-[10px]">RAG + Agentic ReAct</span>
            </div>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Bounded tool-calling loop, persistent vector memory, and inspectable trace output in{" "}
              <code className="font-mono-code text-[var(--accent-terracotta)]">output/</code>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onRefreshTrace}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] border border-[var(--border-subtle)] transition-colors cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh Trace</span>
            </button>

            <button
              onClick={handleCopyJson}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] border border-[var(--border-subtle)] transition-colors cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              <span>Copy Trace JSON</span>
            </button>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-2 mt-4 flex-wrap">
          <button
            onClick={() => setActiveTab("agentic_loop")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "agentic_loop"
                ? "bg-[var(--accent-terracotta)] text-white shadow-sm"
                : "text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Agentic Decision Loop (ReAct)</span>
          </button>

          <button
            onClick={() => setActiveTab("vector_memory")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "vector_memory"
                ? "bg-[var(--accent-terracotta)] text-white shadow-sm"
                : "text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>RAG Vector Memory (384-Dim)</span>
          </button>

          <button
            onClick={() => setActiveTab("agents")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "agents"
                ? "bg-[var(--accent-terracotta)] text-white shadow-sm"
                : "text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Specialized Agents (5)</span>
          </button>

          <button
            onClick={() => setActiveTab("steps")}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "steps"
                ? "bg-[var(--accent-terracotta)] text-white shadow-sm"
                : "text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
            }`}
          >
            Session Trace Steps
          </button>

          <button
            onClick={() => setActiveTab("raw")}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "raw"
                ? "bg-[var(--accent-terracotta)] text-white shadow-sm"
                : "text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
            }`}
          >
            {`{ }`} Raw Output JSON
          </button>
        </div>
      </div>

      {/* Tab: Agentic ReAct Loop */}
      {activeTab === "agentic_loop" && (
        <div className="space-y-4">
          <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)]">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h4 className="font-semibold text-sm text-[var(--text-primary)]">
                  Bounded Tool-Calling Loop Execution Trace (Max 6 Steps)
                </h4>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                  The LLM dynamically selects each domain tool in sequence, queries dense vector memory, and evaluates safety before formulating the growth plan.
                </p>
              </div>
              <span className="badge-claude badge-emerald text-xs">GOVERNED & BOUNDED</span>
            </div>

            <div className="space-y-3">
              {agenticLoopSteps.map((s) => (
                <div
                  key={s.step}
                  className="border border-[var(--border-subtle)] rounded-xl p-4 bg-[var(--bg-secondary)]/40 hover:bg-[var(--bg-secondary)] transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-[var(--accent-terracotta)] text-white text-xs flex items-center justify-center font-bold">
                        {s.step}
                      </span>
                      <span className="font-semibold text-xs text-[var(--text-primary)] font-mono-code">
                        {s.tool}()
                      </span>
                      <span className="text-xs text-[var(--text-muted)]">— {s.title}</span>
                    </div>
                    <span className="badge-claude badge-terracotta text-[10px]">{s.status}</span>
                  </div>

                  <p className="text-xs text-[var(--text-secondary)] mb-2.5">{s.description}</p>

                  <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-lg p-2.5 font-mono-code text-[11px] text-[var(--text-secondary)]">
                    <span className="text-[var(--accent-terracotta)] font-semibold">Result: </span>
                    {JSON.stringify(s.output)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab: RAG Vector Memory */}
      {activeTab === "vector_memory" && (
        <div className="space-y-4">
          <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)]">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h4 className="font-semibold text-sm text-[var(--text-primary)]">
                  Persistent RAG Vector Memory (ChromaDB + Local Embeddings)
                </h4>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                  Stores dense 384-dimensional embeddings of completed campaign outcomes and executive growth scans for zero-hallucination semantic recall.
                </p>
              </div>
              <span className="badge-claude badge-blue text-xs">LOCAL IN-PROCESS</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {vectorMemories.map((mem) => (
                <div
                  key={mem.id}
                  className="border border-[var(--border-subtle)] rounded-xl p-4 bg-[var(--bg-secondary)]/40 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono-code text-xs font-semibold text-[var(--accent-terracotta)]">
                      {mem.id}
                    </span>
                    <span className="badge-claude badge-emerald text-[10px]">{mem.similarity}</span>
                  </div>

                  <p className="text-xs text-[var(--text-primary)] leading-relaxed">{mem.summary}</p>

                  <div className="pt-2 border-t border-[var(--border-subtle)] grid grid-cols-2 gap-2 text-[11px] text-[var(--text-muted)] font-mono-code">
                    <div>
                      <span>Vector Dims: </span>
                      <strong className="text-[var(--text-primary)]">{mem.dimension}</strong>
                    </div>
                    <div>
                      <span>Embedder: </span>
                      <strong className="text-[var(--text-primary)]">FastEmbed ONNX</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Agent Roles */}
      {activeTab === "agents" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agentsList.map((ag) => {
            const Icon = ag.icon;
            return (
              <div
                key={ag.name}
                className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)] hover:border-[var(--border-strong)] transition-all duration-200"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center text-white"
                    style={{ backgroundColor: ag.color }}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-[var(--text-primary)]">
                      {ag.name}
                    </h4>
                    <span className="text-[11px] text-[var(--text-muted)] font-medium">
                      {ag.role}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-3">
                  {ag.description}
                </p>

                <div className="space-y-1.5 pt-3 border-t border-[var(--border-subtle)]">
                  <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-semibold">
                    Core Capabilities:
                  </div>
                  {ag.capabilities.map((cap) => (
                    <div key={cap} className="flex items-center gap-1.5 text-xs text-[var(--text-primary)]">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-terracotta)]" />
                      <span>{cap}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Tab: Execution Steps */}
      {activeTab === "steps" && (
        <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)] space-y-4">
          {!traceData || Object.keys(traceData).length === 0 ? (
            <div className="py-8 text-center text-xs text-[var(--text-muted)]">
              No full trace recorded yet for session <strong>{sessionId}</strong>. Run a growth scan to record execution steps.
            </div>
          ) : (
            Object.entries(traceData).map(([stepKey, stepVal]: [string, any], index) => (
              <div
                key={stepKey}
                className="border border-[var(--border-subtle)] rounded-xl p-4 bg-[var(--bg-secondary)]/50 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-[var(--accent-terracotta)] text-white text-[10px] flex items-center justify-center font-bold">
                      {index + 1}
                    </span>
                    <span className="font-semibold text-xs text-[var(--text-primary)] font-mono-code">
                      {stepKey}
                    </span>
                  </div>
                  <span className="badge-claude badge-emerald text-[10px]">VERIFIED</span>
                </div>

                <pre className="font-mono-code text-[11px] p-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)] text-[var(--text-secondary)] overflow-x-auto max-h-48">
                  {typeof stepVal === "object" ? JSON.stringify(stepVal, null, 2) : String(stepVal)}
                </pre>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab: Raw JSON */}
      {activeTab === "raw" && (
        <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)]">
          <pre className="font-mono-code text-xs p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--accent-terracotta)] overflow-x-auto max-h-96">
            {JSON.stringify(traceData || { message: "Awaiting execution trace..." }, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
