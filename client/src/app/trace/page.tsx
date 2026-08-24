"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Sparkles,
  Layers,
  Brain,
  Wrench,
  ShieldCheck,
  TrendingUp,
  History,
  Play,
  CheckCircle2,
  Clock,
  ArrowLeft,
  ChevronRight,
  Database,
  Users,
  Tag,
  FileText,
  Activity,
  AlertCircle,
  Copy,
  Check,
} from "lucide-react";
import { Header } from "@/components/Header";
import { getLatestTrace, listSessions } from "@/services/api";
import { SessionSummary } from "@/types";

interface LiveStepEvent {
  step: string;
  step_number?: number;
  status: string;
  summary?: string;
  data: any;
  timestamp: string;
}

export default function MultiAgentTracePage() {
  const [sessionId, setSessionId] = useState<string>("");
  const [merchantId, setMerchantId] = useState<string>("merch_demo");
  const [merchantName, setMerchantName] = useState<string>("StyleKart");
  const [traceData, setTraceData] = useState<any>(null);
  const [liveEvents, setLiveEvents] = useState<LiveStepEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamingMode, setStreamingMode] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [activeStepTab, setActiveStepTab] = useState<string>("all");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Initialize session
  useEffect(() => {
    const defaultSess = `sess_${Date.now().toString(36)}`;
    setSessionId(defaultSess);
    loadTrace(defaultSess);
  }, []);

  const loadTrace = async (sid: string) => {
    setIsLoading(true);
    try {
      const res = await getLatestTrace(sid);
      if (res && (res.data || res.steps)) {
        setTraceData(res.data || res);
        if (res.merchant_id) setMerchantId(res.merchant_id);
      } else {
        setTraceData(null);
      }
    } catch (e) {
      console.error("Failed to load trace:", e);
      setTraceData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartLiveStream = (mode: "deterministic" | "agentic") => {
    const activeSess = sessionId || `sess_${Date.now().toString(36)}`;
    setSessionId(activeSess);
    setIsStreaming(true);
    setStreamingMode(mode);
    setLiveEvents([]);

    const base = "http://127.0.0.1:8000/api/v1";
    const endpoint =
      mode === "agentic"
        ? `${base}/growth/agentic-scan-live/${merchantId}?session_id=${activeSess}`
        : `${base}/growth/scan-live/${merchantId}?session_id=${activeSess}`;

    const eventSource = new EventSource(endpoint);

    eventSource.onmessage = (event) => {
      if (event.data === "[DONE]") {
        eventSource.close();
        setIsStreaming(false);
        // Refresh full trace from disk
        loadTrace(activeSess);
        return;
      }

      try {
        const parsed = JSON.parse(event.data);
        setLiveEvents((prev) => [
          ...prev,
          {
            step: parsed.step || "step_event",
            step_number: parsed.step_number || prev.length + 1,
            status: parsed.status || "completed",
            summary: parsed.summary || "",
            data: parsed.data,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
          },
        ]);
      } catch (e) {
        console.error("Error parsing SSE event:", e);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setIsStreaming(false);
      loadTrace(activeSess);
    };
  };

  const handleCopy = (key: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  // Helper to extract trace sections
  const steps = traceData?.steps || {};
  const step2Det = steps["2_opportunity_scan_and_ai_reasoning"]?.data;
  const step2Agentic = steps["2_agentic_decision_loop"]?.data;
  const step3 = steps["3_campaign_launch_and_dispatch"]?.data;
  const step4 = steps["4_experiment_ab_lift_measurement"]?.data;

  // Extract memory citations
  const memoryCitations = step2Agentic?.memory_citations || [];
  const agenticStepsTaken = step2Agentic?.steps_taken || [];
  const opportunities = step2Det?.opportunities || [];
  const actionPlan = step2Det?.action_plan;
  const targetCustomers = actionPlan?.audience?.target_customers || step3?.target_customers || [];

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg-primary)] text-[var(--text-primary)] transition-colors duration-200">
      {/* Header */}
      <Header
        merchantName={merchantName}
        sessionId={sessionId}
        onSelectSession={(sid) => {
          setSessionId(sid);
          loadTrace(sid);
        }}
        onStartDemoTour={() => {}}
        onOpenTerminal={() => {}}
        isTerminalOpen={false}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Top Control Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-subtle)] shadow-[var(--shadow-sm)]">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="p-2 rounded-xl bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)] transition-colors cursor-pointer"
              title="Return to Main Dashboard"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-serif text-lg font-bold text-[var(--text-primary)]">
                  Multi-Agent Live Execution Trace
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[var(--accent-terracotta)] text-white">
                  INSPECTABLE RAG
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)] font-mono">
                Active Trace Context: <strong className="text-[var(--accent-terracotta)]">{sessionId}</strong>
              </p>
            </div>
          </div>

          {/* Streaming Actions */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={() => handleStartLiveStream("agentic")}
              disabled={isStreaming}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[var(--accent-terracotta)] hover:bg-[var(--accent-terracotta-hover)] text-white shadow-xs transition-all cursor-pointer disabled:opacity-50"
            >
              <Sparkles className={`w-3.5 h-3.5 ${isStreaming && streamingMode === "agentic" ? "animate-spin" : ""}`} />
              <span>{isStreaming && streamingMode === "agentic" ? "Streaming Agentic Loop..." : "Live Agentic Scan (SSE)"}</span>
            </button>

            <button
              onClick={() => handleStartLiveStream("deterministic")}
              disabled={isStreaming}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] border border-[var(--border-subtle)] shadow-2xs transition-all cursor-pointer disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 text-[var(--accent-terracotta)] ${isStreaming && streamingMode === "deterministic" ? "animate-spin" : ""}`} />
              <span>{isStreaming && streamingMode === "deterministic" ? "Streaming Multi-Agent..." : "Live Multi-Agent Scan (SSE)"}</span>
            </button>
          </div>
        </div>

        {/* Live SSE Streaming Banner (When active) */}
        {isStreaming && (
          <div className="p-4 rounded-2xl bg-[var(--accent-terracotta-subtle)] border border-[var(--accent-terracotta-border)] shadow-xs animate-in fade-in space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--accent-terracotta)] animate-ping" />
                <span className="text-xs font-bold text-[var(--accent-terracotta)]">
                  Live Multi-Agent Stream Active: Emitting Real-Time Agent Decision Events
                </span>
              </div>
              <span className="text-[11px] font-mono text-[var(--text-muted)]">
                {liveEvents.length} events received
              </span>
            </div>

            <div className="max-h-36 overflow-y-auto space-y-1 pr-1 font-mono text-[11px]">
              {liveEvents.map((evt, i) => (
                <div key={i} className="flex items-center justify-between p-1.5 rounded-lg bg-[var(--bg-card)]/80 text-[var(--text-secondary)] border border-[var(--border-subtle)]">
                  <div className="flex items-center gap-2 truncate">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[var(--accent-emerald)] shrink-0" />
                    <span className="font-bold text-[var(--text-primary)]">{evt.step}</span>
                    <span className="text-[var(--text-muted)] truncate">{evt.summary}</span>
                  </div>
                  <span className="text-[10px] text-[var(--text-muted)] shrink-0 pl-2">{evt.timestamp}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State when no trace exists */}
        {!traceData && !isStreaming && (
          <div className="p-12 text-center rounded-2xl bg-[var(--bg-card)] border border-[var(--border-subtle)] shadow-xs space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-[var(--accent-terracotta-subtle)] text-[var(--accent-terracotta)] flex items-center justify-center mx-auto">
              <Layers className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h3 className="font-serif text-base font-bold text-[var(--text-primary)]">
                No Execution Trace Found for {sessionId}
              </h3>
              <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto">
                Traces are written to disk as agents execute. Click <strong>Live Agentic Scan (SSE)</strong> above or select a historical session from the top dropdown to view its full decision timeline!
              </p>
            </div>
            <button
              onClick={() => handleStartLiveStream("agentic")}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--accent-terracotta)] hover:bg-[var(--accent-terracotta-hover)] text-white shadow-xs transition-all cursor-pointer inline-flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Launch Live Agentic Scan Now</span>
            </button>
          </div>
        )}

        {/* Full Ordered Decision Record Timeline */}
        {traceData && (
          <div className="space-y-6">
            {/* 1. RAG Vector Memory Recall Card (Crucial for Verifying RAG) */}
            {memoryCitations.length > 0 && (
              <div className="p-5 rounded-2xl bg-[var(--bg-card)] border border-emerald-500/30 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-[var(--accent-emerald)]" />
                    <h2 className="font-serif text-sm font-bold text-[var(--text-primary)]">
                      RAG Vector Memory Recall Citations (ChromaDB)
                    </h2>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-[var(--accent-emerald)]">
                    {memoryCitations.length} Past Outcomes Grounded
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)]">
                  These historical campaign benchmarks were dynamically embedded via FastEmbed 384-dim dense vectors and recalled before making decisions.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                  {memoryCitations.map((mem: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-xs space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-[var(--accent-emerald)] text-[11px]">
                          Memory #{idx + 1}
                        </span>
                        {mem.distance !== undefined && (
                          <span className="text-[10px] text-[var(--text-muted)] font-mono">
                            Distance: {mem.distance.toFixed(3)}
                          </span>
                        )}
                      </div>
                      <p className="text-[var(--text-primary)] leading-relaxed">{mem.summary || mem.summary_text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 2. ReAct Step-by-Step Tool Invocations (If Agentic Scan was run) */}
            {agenticStepsTaken.length > 0 && (
              <div className="p-5 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-subtle)] shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Wrench className="w-4 h-4 text-[var(--accent-terracotta)]" />
                    <h2 className="font-serif text-sm font-bold text-[var(--text-primary)]">
                      Autonomous ReAct Tool Invocations ({agenticStepsTaken.length} Steps)
                    </h2>
                  </div>
                  <span className="text-xs font-mono text-[var(--text-muted)]">
                    Bounded Decision Loop
                  </span>
                </div>

                <div className="space-y-3">
                  {agenticStepsTaken.map((step: any, idx: number) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-xs space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-[var(--accent-terracotta)] text-white text-[10px] font-bold flex items-center justify-center">
                            {step.step_number || idx + 1}
                          </span>
                          <span className="font-mono font-bold text-[var(--text-primary)]">
                            {step.tool_name}
                          </span>
                        </div>
                        <span className="text-[11px] text-[var(--text-secondary)] font-medium">
                          {step.step_summary}
                        </span>
                      </div>

                      {/* Tool Arguments & Result Preview */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[10px] font-mono pt-1">
                        <div className="p-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)]">
                          <div className="text-[var(--text-muted)] font-semibold mb-1">Arguments:</div>
                          <div className="text-[var(--text-secondary)] truncate">
                            {JSON.stringify(step.arguments)}
                          </div>
                        </div>
                        <div className="p-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)]">
                          <div className="text-[var(--text-muted)] font-semibold mb-1">Tool Output Result:</div>
                          <div className="text-[var(--text-secondary)] truncate">
                            {JSON.stringify(step.result)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 3. Targeted Audience Cohort (Names, Emails, Segment) */}
            {targetCustomers.length > 0 && (
              <div className="p-5 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-subtle)] shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-blue-500" />
                    <h2 className="font-serif text-sm font-bold text-[var(--text-primary)]">
                      Targeted Audience Cohort ({targetCustomers.length} Customers)
                    </h2>
                  </div>
                  <span className="text-xs font-mono text-blue-500 font-semibold">
                    {actionPlan?.audience?.target_segment || step3?.target_segment || "Target Cohort"}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                  {targetCustomers.slice(0, 9).map((cust: any, i: number) => (
                    <div key={i} className="p-2.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-xs space-y-1">
                      <div className="font-bold text-[var(--text-primary)] truncate">{cust.name}</div>
                      <div className="text-[11px] text-[var(--text-muted)] truncate">{cust.email}</div>
                      <div className="flex items-center justify-between text-[10px] pt-1 text-[var(--text-secondary)]">
                        <span>{cust.favorite_category || "General"}</span>
                        <strong>₹{cust.total_spend ? cust.total_spend.toLocaleString() : "0"}</strong>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 4. A/B Experiment & Webhook Conversions */}
            {step4 && (
              <div className="p-5 rounded-2xl bg-[var(--bg-card)] border border-[var(--accent-terracotta-border)] shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-[var(--accent-emerald)]" />
                    <h2 className="font-serif text-sm font-bold text-[var(--text-primary)]">
                      Live A/B Experiment & Conversion Results
                    </h2>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[var(--accent-emerald)] text-white">
                    Lift: {step4.metrics?.relative_lift_display || "Measured"}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
                    <div className="text-[10px] text-[var(--text-muted)]">Treatment Rate</div>
                    <div className="text-base font-bold text-[var(--accent-emerald)]">
                      {((step4.metrics?.treatment_conversion_rate || 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
                    <div className="text-[10px] text-[var(--text-muted)]">Control Rate</div>
                    <div className="text-base font-bold text-[var(--text-secondary)]">
                      {((step4.metrics?.control_conversion_rate || 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
                    <div className="text-[10px] text-[var(--text-muted)]">Incremental GMV</div>
                    <div className="text-base font-bold text-[var(--accent-terracotta)]">
                      ₹{step4.metrics?.incremental_revenue_inr ? step4.metrics.incremental_revenue_inr.toLocaleString() : "0"}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
                    <div className="text-[10px] text-[var(--text-muted)]">Orders Converted</div>
                    <div className="text-base font-bold text-[var(--text-primary)]">
                      {step4.metrics?.treatment_orders_count || 0}
                    </div>
                  </div>
                </div>

                {/* Converted Customers List */}
                {step4.converted_customers && step4.converted_customers.length > 0 && (
                  <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-xs space-y-1.5">
                    <div className="font-semibold text-[var(--text-primary)] text-[11px]">
                      Converted Customers Verified in PostgreSQL:
                    </div>
                    {step4.converted_customers.map((c: any, i: number) => (
                      <div key={i} className="flex items-center justify-between text-[11px] font-mono text-[var(--text-secondary)]">
                        <span>{c.customer_name} ({c.razorpay_order_id})</span>
                        <strong className="text-[var(--accent-emerald)]">₹{c.amount_paid}</strong>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
