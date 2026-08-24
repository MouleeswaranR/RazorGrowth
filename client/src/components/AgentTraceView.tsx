"use client";

import React, { useState, useEffect } from "react";
import {
  Bot,
  UserCheck,
  Tag,
  Mail,
  Scale,
  Copy,
  Check,
  Database,
  Sparkles,
  Search,
  ShieldCheck,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  CreditCard,
  Play,
  Users,
  Wrench,
  AlertTriangle,
} from "lucide-react";
import { crossReferenceSessions, listSessions, getLatestTrace } from "@/services/api";

/* ── Expandable Step Detail Renderer ───────────────────────────── */

function StepDetailRenderer({ stepName, data }: { stepName: string; data: any }) {
  if (!data) return null;

  // Deep unwrap to get to the actual result object across all step payload variants
  const actualData = data.result !== undefined ? data.result : (data.data !== undefined ? data.data : data);
  const toolArgs = data.arguments || {};

  // 1. Full Agentic ReAct Decision Loop Step
  if (stepName.includes("2_agentic_decision_loop") || stepName.includes("agentic_scan")) {
    const stepsTaken = actualData.steps_taken || actualData.steps || [];
    const planSummary = actualData.plan_summary || actualData.summary || "Autonomous growth plan synthesized across all diagnostic stages.";
    const reasoningTrace = actualData.reasoning_trace || actualData.reasoning;
    const providerUsed = actualData.provider_used;

    return (
      <div className="space-y-3 text-xs">
        {planSummary && (
          <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] leading-relaxed text-[var(--text-primary)]">
            <div className="text-[10px] font-bold text-[var(--accent-terracotta)] uppercase tracking-wider mb-1">Plan Summary</div>
            {planSummary}
          </div>
        )}

        {providerUsed && (
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 font-mono text-[10px]">
              Provider: {providerUsed}
            </span>
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-mono text-[10px]">
              Diagnostic Tools: {stepsTaken.length}
            </span>
          </div>
        )}

        {reasoningTrace && (
          <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 text-[11px] text-[var(--text-secondary)] space-y-1">
            <div className="font-bold text-amber-500 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" /> LLM Strategic Reasoning Trace
            </div>
            <p className="italic leading-relaxed">{reasoningTrace}</p>
          </div>
        )}

        {stepsTaken.length > 0 && (
          <div className="space-y-2 pt-1">
            <div className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
              Diagnostic Tools Executed ({stepsTaken.length})
            </div>
            {stepsTaken.map((st: any, i: number) => (
              <div key={i} className="p-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-[var(--accent-terracotta)] text-white text-[10px] font-bold flex items-center justify-center">
                      {st.step_number || i + 1}
                    </span>
                    <span className="font-mono font-bold text-xs text-[var(--text-primary)]">{st.tool_name}()</span>
                  </div>
                  {st.step_summary && (
                    <span className="text-[10px] text-[var(--text-muted)] font-mono truncate max-w-[60%] text-right">{st.step_summary}</span>
                  )}
                </div>
                <StepDetailRenderer stepName={st.tool_name} data={st.result || st} />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // 1b. Dataset generation step
  if (stepName.includes("1_dataset_generation") || stepName.includes("dataset_generation")) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
        <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
          <div className="text-[10px] text-[var(--text-muted)]">Customers Created</div>
          <div className="text-sm font-bold text-[var(--text-primary)]">{(actualData.customers_created || actualData.total_customers || 500).toLocaleString()}</div>
        </div>
        <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
          <div className="text-[10px] text-[var(--text-muted)]">Orders Created</div>
          <div className="text-sm font-bold text-[var(--text-primary)]">{(actualData.orders_created || actualData.total_orders || 2000).toLocaleString()}</div>
        </div>
        <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
          <div className="text-[10px] text-[var(--text-muted)]">Merchant</div>
          <div className="text-sm font-bold text-[var(--text-primary)] truncate">{actualData.merchant_name || actualData.merchant_id || "StyleKart"}</div>
        </div>
        <div className="p-2.5 rounded-lg bg-emerald-500/5 border border-emerald-500/20 text-center">
          <div className="text-[10px] text-[var(--text-muted)]">Status</div>
          <div className="text-sm font-bold text-emerald-500">✓ Seeded</div>
        </div>
      </div>
    );
  }

  // 2b. Opportunity scan and AI reasoning step
  if (stepName.includes("2_opportunity_scan_and_ai_reasoning") || stepName.includes("opportunity_scan")) {
    const opps = actualData.opportunities || [];
    const actionPlan = actualData.action_plan;
    const llmDecision = actualData.llm_decision;

    return (
      <div className="space-y-3 text-xs">
        {actionPlan?.ai_reasoning && (
          <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] space-y-1.5">
            <div className="text-[10px] font-bold text-[var(--accent-terracotta)] uppercase tracking-wider">AI Reasoning & Executive Diagnosis</div>
            <p className="leading-relaxed text-[var(--text-primary)]">{actionPlan.ai_reasoning}</p>
          </div>
        )}
        {opps.length > 0 && (
          <div className="space-y-2">
            <div className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
              Discovered Opportunities ({opps.length})
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {opps.map((o: any, i: number) => (
                <div key={i} className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)] text-[11px] space-y-1">
                  <div className="font-bold text-[var(--text-primary)] truncate">{o.title}</div>
                  <div className="flex justify-between text-[10px] text-[var(--text-muted)]">
                    <span>{o.type}</span>
                    <strong className="text-[var(--accent-emerald)]">₹{Number(o.estimated_gmv || 0).toLocaleString()}</strong>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        {llmDecision && (
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 font-mono text-[10px]">
              Model: {llmDecision.model_name || "Llama-3.3 70B"}
            </span>
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-mono text-[10px]">
              Provider: {llmDecision.provider_used || "nvidia_nim"}
            </span>
          </div>
        )}
      </div>
    );
  }

  // 3b. Campaign launch & dispatch step
  if (stepName.includes("3_campaign_launch") || stepName.includes("campaign_launch")) {
    const offer = actualData.offer || {};

    return (
      <div className="space-y-3 text-xs">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
            <div className="text-[10px] text-[var(--text-muted)]">Total Audience</div>
            <div className="text-sm font-bold text-[var(--text-primary)]">{actualData.total_audience || 0}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
            <div className="text-[10px] text-[var(--text-muted)]">Treatment (80%)</div>
            <div className="text-sm font-bold text-[var(--accent-emerald)]">{actualData.treatment_group_size || 0}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
            <div className="text-[10px] text-[var(--text-muted)]">Control (20%)</div>
            <div className="text-sm font-bold text-[var(--text-secondary)]">{actualData.control_group_size || 0}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
            <div className="text-[10px] text-[var(--text-muted)]">Dispatched</div>
            <div className="text-sm font-bold text-blue-500">{actualData.emails_dispatched || 0} msgs</div>
          </div>
        </div>
        {offer.offer_code && (
          <div className="flex items-center gap-2 text-[11px] p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)]">
            <span className="font-bold text-[var(--text-muted)]">Incentive:</span>
            <span className="px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 font-mono font-bold">{offer.offer_code}</span>
            <span className="font-bold text-[var(--accent-terracotta)]">{offer.discount_value}% OFF</span>
            {offer.min_order_value && <span className="text-[var(--text-muted)] font-mono">(Min Order: ₹{offer.min_order_value})</span>}
          </div>
        )}
      </div>
    );
  }

  // 4b. Experiment AB lift measurement step
  if (stepName.includes("4_experiment_ab_lift_measurement") || stepName.includes("experiment_ab")) {
    const metrics = actualData.metrics || {};
    const converted = actualData.converted_customers || [];

    return (
      <div className="space-y-3 text-xs">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
            <div className="text-[10px] text-[var(--text-muted)]">Treatment Rate</div>
            <div className="text-sm font-bold text-[var(--accent-emerald)]">{((metrics.treatment_conversion_rate || 0) * 100).toFixed(2)}%</div>
          </div>
          <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
            <div className="text-[10px] text-[var(--text-muted)]">Control Rate</div>
            <div className="text-sm font-bold text-[var(--text-secondary)]">{((metrics.control_conversion_rate || 0) * 100).toFixed(2)}%</div>
          </div>
          <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
            <div className="text-[10px] text-[var(--text-muted)]">Relative Lift</div>
            <div className="text-sm font-bold text-[var(--accent-emerald)]">{metrics.relative_lift_display || "N/A"}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
            <div className="text-[10px] text-[var(--text-muted)]">Incremental GMV</div>
            <div className="text-sm font-bold text-[var(--accent-emerald)]">₹{Number(metrics.incremental_revenue_inr || 0).toLocaleString()}</div>
          </div>
        </div>
        {converted.length > 0 && (
          <div className="space-y-1">
            <div className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Converted Customers ({converted.length})</div>
            <div className="flex flex-wrap gap-1.5">
              {converted.map((c: any, i: number) => (
                <span key={i} className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-mono text-emerald-500">
                  {c.customer_id || c.name || `Customer #${i + 1}`} · ₹{Number(c.amount || c.spend || 0).toLocaleString()}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // 6b. Vector memory persisted step
  if (stepName.includes("6_rag_vector_memory") || stepName.includes("memory_persisted")) {
    return (
      <div className="space-y-2 text-xs">
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-lg bg-blue-500/10 text-blue-500 font-mono font-bold text-[10px]">
            ChromaDB 384-Dim
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-500 font-mono font-bold text-[10px]">
            Vector Stored
          </span>
        </div>
        {actualData.summary && (
          <p className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] leading-relaxed text-[var(--text-primary)]">
            {actualData.summary}
          </p>
        )}
      </div>
    );
  }

  // 2. Vector memory recall step
  if (stepName.includes("vector_memory_recall") || stepName.includes("recall_similar_past_campaigns")) {
    const memories = actualData.retrieved_memories || actualData.memories || [];
    const query = actualData.query || toolArgs.query || "";
    return (
      <div className="space-y-2">
        {query && (
          <div className="text-[11px] text-[var(--text-muted)]">
            Search Query: <code className="px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] text-[var(--text-primary)]">{query}</code>
          </div>
        )}
        {memories.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {memories.map((mem: any, i: number) => (
              <div key={i} className="p-2.5 rounded-lg bg-emerald-500/5 border border-emerald-500/20 text-[11px] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-emerald-500 font-mono">Memory #{i + 1}</span>
                  {mem.distance !== undefined && (
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">dist: {typeof mem.distance === "number" ? mem.distance.toFixed(4) : String(mem.distance)}</span>
                  )}
                </div>
                <p className="text-[var(--text-primary)] leading-relaxed">{mem.summary || mem.summary_text}</p>
                {mem.metadata && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {Object.entries(mem.metadata).map(([k, v]: [string, any]) => (
                      <span key={k} className="px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] text-[10px] text-[var(--text-muted)] font-mono">
                        {k}: <strong className="text-[var(--text-primary)]">{typeof v === "number" ? v.toLocaleString() : String(v)}</strong>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[11px] text-[var(--text-muted)]">
            No historical campaign memories found in ChromaDB for this query.
          </div>
        )}
      </div>
    );
  }

  // 3. Merchant context / telemetry step
  if (stepName.includes("merchant_context") || stepName.includes("telemetry") || stepName.includes("1_dataset_generation")) {
    const totalCustomers = actualData.total_customers || actualData.customers_created || actualData.customer_count;
    const totalRev = actualData.total_revenue_inr !== undefined ? actualData.total_revenue_inr : (actualData.total_gmv !== undefined ? actualData.total_gmv : actualData.total_spend);
    const payRate = actualData.payment_overall_success_rate !== undefined ? actualData.payment_overall_success_rate : actualData.payment_success_rate;
    const dormantVips = actualData.dormant_vip_count !== undefined ? actualData.dormant_vip_count : actualData.dormant_count;

    const metricsList = [
      { label: "Total Customers", value: totalCustomers ? Number(totalCustomers).toLocaleString() : undefined },
      { label: "Total GMV", value: totalRev !== undefined ? `₹${Number(totalRev).toLocaleString()}` : undefined },
      { label: "Payment Success", value: payRate !== undefined ? `${(Number(payRate) * 100).toFixed(1)}%` : undefined },
      { label: "Dormant VIPs", value: dormantVips !== undefined ? Number(dormantVips).toLocaleString() : undefined },
    ].filter((m) => m.value !== undefined);

    return (
      <div className="space-y-2">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {metricsList.map((m, i) => (
            <div key={i} className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
              <div className="text-[10px] text-[var(--text-muted)]">{m.label}</div>
              <div className="text-sm font-bold text-[var(--text-primary)]">{m.value}</div>
            </div>
          ))}
        </div>
        {(actualData.segment_breakdown || actualData.segment_distribution) && typeof (actualData.segment_breakdown || actualData.segment_distribution) === "object" && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {Object.entries(actualData.segment_breakdown || actualData.segment_distribution).map(([k, v]: [string, any]) => (
              <span key={k} className="px-2 py-0.5 rounded-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[10px] font-mono text-[var(--text-secondary)]">
                {k}: <strong className="text-[var(--text-primary)]">{String(v)}</strong>
              </span>
            ))}
          </div>
        )}
      </div>
    );
  }

  // 4. Opportunities detected step
  if (stepName.includes("opportunities") || stepName.includes("detect_opportunities")) {
    const opps = actualData.opportunities || [];
    const count = actualData.opportunities_found !== undefined ? actualData.opportunities_found : opps.length;
    return (
      <div className="space-y-2">
        <div className="text-[11px] text-[var(--text-muted)] font-mono">
          Identified <strong className="text-[var(--accent-terracotta)]">{count}</strong> potential growth opportunities:
        </div>
        {opps.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {opps.map((o: any, i: number) => (
              <div key={i} className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[11px] space-y-1">
                <div className="font-bold text-[var(--text-primary)]">{o.title}</div>
                <div className="flex flex-wrap gap-2 text-[10px] text-[var(--text-muted)]">
                  {o.type && <span>Type: <strong className="text-[var(--text-secondary)]">{o.type}</strong></span>}
                  {o.audience_count !== undefined && <span>Audience: <strong className="text-[var(--text-secondary)]">{o.audience_count}</strong></span>}
                  {o.estimated_gmv !== undefined && <span>GMV: <strong className="text-[var(--accent-emerald)]">₹{Number(o.estimated_gmv || 0).toLocaleString()}</strong></span>}
                  {o.confidence !== undefined && <span>Conf: <strong className="text-blue-500">{((Number(o.confidence) || 0) * 100).toFixed(0)}%</strong></span>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[11px] text-[var(--text-muted)]">
            Diagnostic scan complete. No critical revenue leaks detected.
          </div>
        )}
      </div>
    );
  }

  // 5. Audience selected step
  if (stepName.includes("audience") || stepName.includes("select_audience")) {
    const targetSegment = actualData.target_segment || actualData.segment || toolArgs.opportunity_type || "VIP Dormant";
    const audienceCount = actualData.audience_count !== undefined ? actualData.audience_count : (actualData.total_audience_count !== undefined ? actualData.total_audience_count : (actualData.target_customers ? actualData.target_customers.length : 0));
    const avgSpend = actualData.avg_spend || actualData.average_spend;
    const reasoning = actualData.reasoning || actualData.audience_reasoning;
    const customers = actualData.target_customers || [];

    return (
      <div className="space-y-2">
        <div className="flex flex-wrap gap-3 text-[11px] p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)]">
          <span className="text-[var(--text-muted)]">Segment: <strong className="text-[var(--accent-terracotta)]">{targetSegment}</strong></span>
          <span className="text-[var(--text-muted)]">Target Audience: <strong className="text-[var(--text-primary)]">{audienceCount} customers</strong></span>
          {avgSpend !== undefined && <span className="text-[var(--text-muted)]">Avg Spend: <strong className="text-[var(--text-primary)]">₹{Number(avgSpend).toLocaleString()}</strong></span>}
        </div>
        {reasoning && (
          <p className="text-[11px] text-[var(--text-secondary)] italic leading-relaxed">{reasoning}</p>
        )}
        {customers.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
            {customers.slice(0, 6).map((c: any, i: number) => (
              <div key={i} className="p-1.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[10px] truncate">
                <span className="font-semibold text-[var(--text-primary)]">{c.name}</span>
                <span className="text-[var(--text-muted)]"> · ₹{Number(c.total_spend || 0).toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // 6. Offer recommended step
  if (stepName.includes("offer") || stepName.includes("recommend_offer")) {
    const offerCode = actualData.offer_code || "VIP20OFF";
    const discountVal = actualData.discount_value !== undefined ? actualData.discount_value : (actualData.discount_percentage || 20);
    const description = actualData.description || actualData.offer_details || "Promotional incentive calibrated for customer cohort.";
    const urgency = actualData.urgency_text || actualData.urgency || "Expires in 7 days";
    const minOrder = actualData.min_order_value || actualData.minimum_order_value;

    return (
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-2 text-[11px]">
          {offerCode && <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-500 font-mono font-bold">{offerCode}</span>}
          {discountVal !== undefined && <span className="px-2 py-0.5 rounded-full bg-[var(--accent-terracotta)] text-white text-[10px] font-bold">{discountVal}% OFF</span>}
          {urgency && <span className="text-[var(--text-muted)] italic text-[10px]">{urgency}</span>}
        </div>
        {description && <p className="text-xs text-[var(--text-primary)] leading-relaxed font-medium">{description}</p>}
        {minOrder !== undefined && minOrder > 0 && (
          <div className="text-[10px] text-[var(--text-muted)] font-mono">Min. Order Value: ₹{Number(minOrder).toLocaleString()}</div>
        )}
      </div>
    );
  }

  // 7. Permission gate check step
  if (stepName.includes("permission_gate") || stepName.includes("check_permission")) {
    const isSafe = actualData.is_safe || actualData.policy_status === "auto_approved" || actualData.status === "auto_approved" || (typeof actualData.status?.value === "string" && actualData.status.value === "auto_approved");
    const policyNotes = actualData.policy_notes || (isSafe ? "Campaign parameters are within store GMV threshold and discount caps." : "Campaign requires merchant manual authorization.");
    const thresholds = actualData.thresholds || {};

    return (
      <div className="space-y-2 text-[11px]">
        <div className="flex items-center gap-2">
          <span className={`px-2.5 py-1 rounded-lg font-bold text-xs ${isSafe ? "bg-emerald-500/10 text-emerald-500" : "bg-amber-500/10 text-amber-500"}`}>
            {isSafe ? "✓ Auto-Approved" : "⚠ Requires Merchant Review"}
          </span>
          <span className="text-[var(--text-muted)] font-mono text-[10px]">
            {isSafe ? "Risk Score: Low" : "Risk Score: Elevated"}
          </span>
        </div>
        {policyNotes && <p className="text-[var(--text-secondary)] leading-relaxed">{policyNotes}</p>}
        {Object.keys(thresholds).length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {Object.entries(thresholds).map(([k, v]: [string, any]) => (
              <span key={k} className="px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] text-[10px] font-mono text-[var(--text-muted)]">
                {k}: <strong className="text-[var(--text-primary)]">{typeof v === "number" ? v.toFixed(1) : String(v)}</strong>
              </span>
            ))}
          </div>
        )}
      </div>
    );
  }

  // 8. Copy composed step
  if (stepName.includes("copy")) {
    return (
      <div className="space-y-1 text-[11px]">
        {actualData.email_subject && <div className="text-[var(--text-muted)]">Subject: <strong className="text-[var(--text-primary)]">{actualData.email_subject}</strong></div>}
        {actualData.email_body && <div className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-primary)] whitespace-pre-line leading-relaxed">{actualData.email_body}</div>}
        {actualData.whatsapp_message && <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/20 text-[var(--text-primary)] whitespace-pre-line leading-relaxed">{actualData.whatsapp_message}</div>}
      </div>
    );
  }

  // 9. Final plan synthesized step
  if (stepName.includes("plan") || stepName.includes("final")) {
    const planSummary = actualData.plan_summary || actualData.summary || "Autonomous growth plan completed across all domain tools.";
    const providerUsed = actualData.provider_used;
    const reasoningTrace = actualData.reasoning_trace;
    const stepsTaken = actualData.steps_taken || [];

    return (
      <div className="space-y-2 text-[11px]">
        <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] leading-relaxed text-[var(--text-primary)]">
          {planSummary}
        </div>
        <div className="flex items-center gap-2">
          {providerUsed && <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 text-[10px] font-mono">Provider: {providerUsed}</span>}
          {stepsTaken.length > 0 && <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-mono">{stepsTaken.length} Steps Completed</span>}
        </div>
        {reasoningTrace && (
          <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-muted)] italic leading-relaxed">
            {reasoningTrace}
          </div>
        )}
      </div>
    );
  }

  // 10. Webhook / payment step
  if (stepName.includes("payment") || stepName.includes("webhook")) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
        {actualData.payment_id && <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/20"><div className="text-[10px] text-[var(--text-muted)]">Payment ID</div><div className="font-mono font-bold text-[var(--text-primary)] truncate">{actualData.payment_id}</div></div>}
        {(actualData.amount_inr || actualData.amount) && <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/20"><div className="text-[10px] text-[var(--text-muted)]">Amount</div><div className="font-bold text-emerald-500">₹{Number(actualData.amount_inr || actualData.amount || 0).toLocaleString()}</div></div>}
        {actualData.customer_id && <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/20"><div className="text-[10px] text-[var(--text-muted)]">Customer</div><div className="font-mono text-[var(--text-primary)] truncate">{actualData.customer_id}</div></div>}
        {actualData.measured_via && <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/20"><div className="text-[10px] text-[var(--text-muted)]">Attribution</div><div className="font-semibold text-[var(--text-primary)]">{actualData.measured_via}</div></div>}
      </div>
    );
  }

  // Default: formatted JSON with key-value pills for shallow objects
  const entries = Object.entries(actualData);
  if (entries.length <= 12 && entries.every(([, v]) => typeof v !== "object" || v === null)) {
    return (
      <div className="flex flex-wrap gap-1.5">
        {entries.map(([k, v]: [string, any]) => (
          <span key={k} className="px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] text-[10px] font-mono text-[var(--text-muted)]">
            {k}: <strong className="text-[var(--text-primary)]">{typeof v === "number" ? v.toLocaleString() : String(v)}</strong>
          </span>
        ))}
      </div>
    );
  }

  return (
    <pre className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] font-mono text-[11px] text-[var(--text-secondary)] overflow-x-auto whitespace-pre-wrap">
      {JSON.stringify(actualData, null, 2)}
    </pre>
  );
}

/* ── Expandable Step Card ─────────────────────────────────────── */

function ExpandableStepCard({
  stepKey,
  stepData,
  index,
  recordedAt,
  elapsedLabel,
}: {
  stepKey: string;
  stepData: any;
  index: number;
  recordedAt?: string;
  elapsedLabel?: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const isWebhookStep = stepKey.includes("payment") || stepKey.includes("webhook");
  const isVectorStep = stepKey.includes("vector_memory") || stepKey.includes("recall");

  return (
    <div className="rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-3.5 flex items-center justify-between hover:bg-[var(--bg-card-hover)] transition-all cursor-pointer"
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="w-5 h-5 rounded-full bg-[var(--accent-terracotta)] text-white text-[10px] font-bold flex items-center justify-center shrink-0">
            {index + 1}
          </span>
          <span className="text-xs font-bold text-[var(--text-primary)] font-mono truncate">{stepKey}</span>
          {isWebhookStep && <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/10 text-emerald-500 font-bold shrink-0">✓ Webhook</span>}
          {isVectorStep && <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono bg-blue-500/10 text-blue-500 font-bold shrink-0">🧠 ChromaDB</span>}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {elapsedLabel && <span className="px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] text-[10px] font-mono text-[var(--text-muted)]">{elapsedLabel}</span>}
          {recordedAt && <span className="text-[10px] font-mono text-[var(--text-muted)]" suppressHydrationWarning>{new Date(recordedAt).toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" })}</span>}
          {expanded ? <ChevronUp className="w-3.5 h-3.5 text-[var(--text-muted)]" /> : <ChevronDown className="w-3.5 h-3.5 text-[var(--text-muted)]" />}
        </div>
      </button>
      {expanded && (
        <div className="px-3.5 pb-3.5 pt-1 border-t border-[var(--border-subtle)] animate-in fade-in">
          <StepDetailRenderer stepName={stepKey} data={stepData} />
        </div>
      )}
    </div>
  );
}

/* ── Interfaces ───────────────────────────────────────────────── */

interface LiveStepEvent {
  step: string;
  step_number?: number;
  status: string;
  summary?: string;
  data: any;
  timestamp: string;
}

interface AgentTraceViewProps {
  traceData: any;
  sessionId: string;
  merchantId?: string;
  onRefreshTrace: () => void;
}

/* ── Main Component ───────────────────────────────────────────── */

export const AgentTraceView: React.FC<AgentTraceViewProps> = ({
  traceData: initialTraceData,
  sessionId,
  merchantId,
  onRefreshTrace,
}) => {
  const [activeTab, setActiveTab] = useState<"all" | "agentic_loop" | "vector_memory" | "steps" | "raw">("all");
  const [traceData, setTraceData] = useState<any>(initialTraceData);
  const [copied, setCopied] = useState(false);
  const [showAgentsGuide, setShowAgentsGuide] = useState(false);

  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMode, setStreamingMode] = useState("");
  const [streamError, setStreamError] = useState("");
  const [liveEvents, setLiveEvents] = useState<LiveStepEvent[]>([]);
  const [expandedLiveIdx, setExpandedLiveIdx] = useState<number | null>(null);

  const [ragQuery, setRagQuery] = useState("dormant customer recovery discount");
  const [targetSessionId, setTargetSessionId] = useState("");
  const [availableSessions, setAvailableSessions] = useState<any[]>([]);
  const [ragResults, setRagResults] = useState<any[]>([]);
  const [comparisonNarrative, setComparisonNarrative] = useState("");
  const [isSearchingRag, setIsSearchingRag] = useState(false);

  useEffect(() => { setTraceData(initialTraceData); }, [initialTraceData]);

  useEffect(() => {
    listSessions()
      .then((res) => { if (res.status === "success") setAvailableSessions(res.sessions.filter((s) => s.session_id !== sessionId)); })
      .catch(() => {});
  }, [sessionId]);

  const loadLatestTrace = async (sid: string) => {
    try {
      const res = await getLatestTrace(sid);
      if (res?.data) setTraceData(res.data);
      else if (res?.steps) setTraceData(res);
    } catch (e) { console.warn("Failed to reload trace:", e); }
  };

  const handleStartLiveStream = (mode: "deterministic" | "agentic") => {
    const activeSess = sessionId || `sess_${Date.now().toString(36)}`;
    // Prefer the dashboard's active merchant; fall back to the loaded trace. Never
    // stream against a placeholder id, which would yield an empty 0-customer scan.
    const activeMerchant = merchantId || traceData?.merchant_id || "";
    if (!activeMerchant || activeMerchant === "merch_demo") {
      setStreamError(
        "No active merchant yet. Generate a dataset (or load a past session) first, then start the live scan."
      );
      return;
    }

    setStreamError("");
    setIsStreaming(true);
    setStreamingMode(mode);
    setLiveEvents([]);
    setExpandedLiveIdx(null);

    const base = "http://127.0.0.1:8000/api/v1";
    const endpoint = mode === "agentic"
      ? `${base}/growth/agentic-scan-live/${activeMerchant}?session_id=${activeSess}`
      : `${base}/growth/scan-live/${activeMerchant}?session_id=${activeSess}`;

    const eventSource = new EventSource(endpoint);
    eventSource.onmessage = (event) => {
      if (event.data === "[DONE]") {
        eventSource.close();
        setIsStreaming(false);
        loadLatestTrace(activeSess);
        onRefreshTrace();
        return;
      }
      try {
        const parsed = JSON.parse(event.data);
        setLiveEvents((prev) => [...prev, {
          step: parsed.step || "step_event",
          step_number: parsed.step_number || 1,
          status: parsed.status || "completed",
          summary: parsed.summary || "",
          data: parsed.data,
          timestamp: new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" }),
        }]);
        if (parsed.step === "final_plan_synthesized" || parsed.step === "7_growth_plan_finalized") {
          setTraceData((prev: any) => ({
            ...prev, merchant_id: activeMerchant,
            steps: { ...(prev?.steps || {}),
              ...(mode === "agentic" ? { "2_agentic_decision_loop": { data: parsed.data } } : { "2_opportunity_scan_and_ai_reasoning": { data: parsed.data } }),
            },
          }));
        }
      } catch (e) { console.error("SSE parse error:", e); }
    };
    eventSource.onerror = () => { eventSource.close(); setIsStreaming(false); loadLatestTrace(activeSess); onRefreshTrace(); };
  };

  const handleSearchRag = async () => {
    setIsSearchingRag(true);
    try {
      const res = await crossReferenceSessions(sessionId, targetSessionId || undefined, ragQuery);
      if (res.status === "success") { setRagResults(res.vector_memories || []); setComparisonNarrative(res.comparison_narrative || ""); }
    } catch (err) { console.error("RAG search failed:", err); }
    finally { setIsSearchingRag(false); }
  };

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(traceData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isBusy = isStreaming || isSearchingRag;

  // Trace extraction
  const stepsObj = traceData?.steps || {};
  const getStepOrder = (key: string): number => {
    const match = key.match(/(\d+)/);
    if (match) return parseInt(match[1], 10);
    if (key.includes("final")) return 100;
    return 999;
  };
  const sortedStepKeys = Object.keys(stepsObj).sort((a, b) => getStepOrder(a) - getStepOrder(b));

  const step2Det = stepsObj["2_opportunity_scan_and_ai_reasoning"]?.data;
  const step2Agentic = stepsObj["2_agentic_decision_loop"]?.data;
  const step4 = stepsObj["4_experiment_ab_lift_measurement"]?.data;
  const step5 = stepsObj["5_razorpay_test_payment_captured"]?.data;

  // Extract agentic steps either from 2_agentic_decision_loop or from individual step_* records
  let agenticStepsTaken: any[] = step2Agentic?.steps_taken || [];
  if (agenticStepsTaken.length === 0) {
    const individualStepKeys = Object.keys(stepsObj).filter((k) => k.startsWith("step_"));
    if (individualStepKeys.length > 0) {
      agenticStepsTaken = individualStepKeys
        .sort((a, b) => getStepOrder(a) - getStepOrder(b))
        .map((k) => {
          const raw = stepsObj[k]?.data || {};
          const toolName = raw.tool_name || k.replace(/^step_\d+_/, "");
          return {
            tool_name: toolName,
            step_summary: raw.step_summary || raw.summary || `Executed ${toolName}`,
            arguments: raw.arguments || {},
            result: raw.result !== undefined ? raw.result : raw,
          };
        });
    }
  }
  const memoryCitations: any[] = step2Agentic?.memory_citations || step2Det?.memory_citations || [];
  const targetCustomers = step2Det?.action_plan?.audience?.target_customers || stepsObj["3_campaign_launch_and_dispatch"]?.data?.target_customers || [];

  // Agent architecture with tools & modes
  const agentsArchitectureList = [
    { name: "GrowthManagerAgent", role: "Strategic Orchestrator", icon: Bot,
      description: "Master orchestrator coordinating opportunity detection, sub-agent delegation, and permission gate validation.",
      tools: ["Orchestrates all 6 domain tools sequentially"], modes: ["deterministic", "agentic"] },
    { name: "CustomerAgent", role: "Audience & Cohort Specialist", icon: UserCheck,
      description: "Filters and ranks target cohorts using empirical spend percentiles (P90), churn intervals, and predictive CLV.",
      tools: ["select_audience(opportunity_type)"], modes: ["deterministic", "agentic"] },
    { name: "OfferAgent", role: "Incentive & Pricing Strategist", icon: Tag,
      description: "Calibrates margin-safe promotional incentives (VIP20OFF, WELCOME15, UPISWIFT, BUNDLE10) with budget limits.",
      tools: ["recommend_offer(segment, average_spend)"], modes: ["deterministic", "agentic"] },
    { name: "CampaignAgent", role: "Multichannel Copywriter", icon: Mail,
      description: "Generates personalized Email & WhatsApp notifications referencing historical purchase categories.",
      tools: ["compose_personalized_copy(...)"], modes: ["deterministic"] },
    { name: "ExperimentAgent", role: "A/B Science & Lift Evaluator", icon: Scale,
      description: "Randomizes 80/20 cohort splits and computes mathematical conversion lift from Razorpay webhooks.",
      tools: ["create_cohort_test_orders", "recalculate_campaign_metrics"], modes: ["deterministic"] },
    { name: "PermissionGateService", role: "Deterministic Safety Firewall", icon: ShieldCheck,
      description: "Enforces non-negotiable financial guardrails (20% max discount, 5% store GMV budget) before campaign dispatch.",
      tools: ["check_permission_gate(discount_value, audience_count)"], modes: ["deterministic", "agentic"] },
  ];

  return (
    <div className="space-y-6">
      {/* Top Control Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-subtle)] shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[var(--accent-terracotta)]" />
            <h2 className="font-serif text-lg font-bold text-[var(--text-primary)]">
              Multi-Agent Live Execution Trace & RAG Explorer
            </h2>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[var(--accent-terracotta)] text-white">LIVE</span>
          </div>
          <p className="text-xs text-[var(--text-secondary)]">
            Session: <code className="px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] font-mono text-[var(--accent-terracotta)] font-bold">{sessionId}</code>
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button onClick={() => handleStartLiveStream("agentic")} disabled={isBusy}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[var(--accent-terracotta)] hover:bg-[var(--accent-terracotta-hover)] text-white shadow-xs transition-all cursor-pointer disabled:opacity-50">
            <Sparkles className={`w-3.5 h-3.5 ${isStreaming && streamingMode === "agentic" ? "animate-spin" : ""}`} />
            {isStreaming && streamingMode === "agentic" ? "Streaming ReAct Loop..." : "Live Agentic Scan (SSE)"}
          </button>
          <button onClick={() => handleStartLiveStream("deterministic")} disabled={isBusy}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] border border-[var(--border-subtle)] transition-all cursor-pointer disabled:opacity-50">
            <Play className={`w-3.5 h-3.5 text-[var(--accent-terracotta)] ${isStreaming && streamingMode === "deterministic" ? "animate-spin" : ""}`} />
            {isStreaming && streamingMode === "deterministic" ? "Streaming Multi-Agent..." : "Live Multi-Agent Scan (SSE)"}
          </button>
          <button onClick={handleCopyJson} className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-subtle)] text-xs font-semibold text-[var(--text-primary)] transition-all cursor-pointer">
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "Copied" : "Copy JSON"}
          </button>
        </div>
      </div>

      {/* Live stream pre-flight guard message */}
      {streamError && (
        <div className="flex items-center gap-2 p-3 rounded-2xl bg-amber-500/5 border border-amber-500/25 text-xs text-[var(--text-primary)]">
          <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
          <span>{streamError}</span>
        </div>
      )}

      {/* Live SSE Streaming Events — Expandable Steps */}
      {(isStreaming || liveEvents.length > 0) && (
        <div className="p-4 rounded-2xl bg-[var(--accent-terracotta-subtle)] border border-[var(--accent-terracotta-border)] shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {isStreaming ? (
                <><span className="w-2.5 h-2.5 rounded-full bg-[var(--accent-terracotta)] animate-ping" /><span className="text-xs font-bold text-[var(--accent-terracotta)]">Live Stream Active — Emitting Agent Decision Events</span></>
              ) : (
                <><CheckCircle2 className="w-4 h-4 text-[var(--accent-emerald)]" /><span className="text-xs font-bold text-[var(--text-primary)]">Execution Complete ({liveEvents.length} Events)</span></>
              )}
            </div>
            <span className="text-[11px] font-mono text-[var(--text-muted)]">{liveEvents.length} steps</span>
          </div>
          <div className="max-h-[400px] overflow-y-auto space-y-1.5 pr-1">
            {liveEvents.map((evt, i) => (
              <div key={i} className="rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] overflow-hidden">
                <button onClick={() => setExpandedLiveIdx(expandedLiveIdx === i ? null : i)}
                  className="w-full p-2.5 flex items-center justify-between hover:bg-[var(--bg-card-hover)] transition-all cursor-pointer text-[11px]">
                  <div className="flex items-center gap-2 min-w-0 truncate">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[var(--accent-emerald)] shrink-0" />
                    <span className="font-bold text-[var(--text-primary)] font-mono">{evt.step}</span>
                    <span className="text-[var(--text-muted)] truncate">{evt.summary}</span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className="text-[10px] text-[var(--text-muted)]">{evt.timestamp}</span>
                    {expandedLiveIdx === i ? <ChevronUp className="w-3 h-3 text-[var(--text-muted)]" /> : <ChevronDown className="w-3 h-3 text-[var(--text-muted)]" />}
                  </div>
                </button>
                {expandedLiveIdx === i && evt.data && (
                  <div className="px-3 pb-3 pt-1 border-t border-[var(--border-subtle)]">
                    <StepDetailRenderer stepName={evt.step} data={evt.data} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] pb-2 overflow-x-auto text-xs">
        {([
          { key: "all", label: "📋 All Trace Overview" },
          { key: "agentic_loop", label: `⚡ ReAct Loop (${agenticStepsTaken.length > 0 ? `${agenticStepsTaken.length} Tools` : (step2Det ? "Pipeline Active" : "0 Tools")})` },
          { key: "vector_memory", label: "🧠 RAG Vector Memory Lab" },
          { key: "steps", label: `📜 Session Steps (${sortedStepKeys.length})` },
          { key: "raw", label: "Raw JSON" },
        ] as { key: typeof activeTab; label: string }[]).map((tab) => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            className={`px-3.5 py-1.5 rounded-xl font-semibold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === tab.key
                ? "bg-[var(--accent-terracotta)] text-white shadow-xs"
                : "bg-[var(--bg-card)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] border border-[var(--border-subtle)]"
            }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB: ALL TRACE OVERVIEW */}
      {activeTab === "all" && (
        <div className="space-y-6">
          {memoryCitations.length > 0 && (
            <div className="p-5 rounded-2xl bg-[var(--bg-card)] border border-emerald-500/30 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2"><Database className="w-4 h-4 text-[var(--accent-emerald)]" /><h2 className="font-serif text-sm font-bold">RAG Vector Memory Citations</h2></div>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-[var(--accent-emerald)]">{memoryCitations.length} Recalled</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {memoryCitations.map((mem: any, idx: number) => (
                  <div key={idx} className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-[var(--accent-emerald)]">Memory #{idx + 1}</span>
                      {mem.distance !== undefined && <span className="text-[10px] text-[var(--text-muted)] font-mono">dist: {typeof mem.distance === "number" ? mem.distance.toFixed(3) : String(mem.distance)}</span>}
                    </div>
                    <p className="text-[var(--text-primary)] leading-relaxed">{mem.summary || mem.summary_text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          {targetCustomers.length > 0 && (
            <div className="p-5 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-subtle)] shadow-xs space-y-3">
              <div className="flex items-center gap-2"><Users className="w-4 h-4 text-blue-500" /><h2 className="font-serif text-sm font-bold">Targeted Audience ({targetCustomers.length})</h2></div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {targetCustomers.slice(0, 9).map((c: any, i: number) => (
                  <div key={i} className="p-2 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-xs">
                    <div className="font-bold text-[var(--text-primary)] truncate">{c.name}</div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">{c.email}</div>
                    <div className="flex justify-between text-[10px] pt-0.5"><span>{c.favorite_category || "General"}</span><strong>₹{Number(c.total_spend || 0).toLocaleString()}</strong></div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {step4 && (
            <div className="p-5 rounded-2xl bg-[var(--bg-card)] border border-[var(--accent-terracotta-border)] shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2"><TrendingUp className="w-4 h-4 text-[var(--accent-emerald)]" /><h2 className="font-serif text-sm font-bold">A/B Experiment Results</h2></div>
                <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-[var(--accent-emerald)] text-white">Lift: {step4.metrics?.relative_lift_display || "Measured"}</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center"><div className="text-[10px] text-[var(--text-muted)]">Treatment</div><div className="text-base font-bold text-[var(--accent-emerald)]">{((step4.metrics?.treatment_conversion_rate || 0) * 100).toFixed(1)}%</div></div>
                <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center"><div className="text-[10px] text-[var(--text-muted)]">Control</div><div className="text-base font-bold text-[var(--text-secondary)]">{((step4.metrics?.control_conversion_rate || 0) * 100).toFixed(1)}%</div></div>
                <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center"><div className="text-[10px] text-[var(--text-muted)]">+Orders</div><div className="text-base font-bold">+{step4.metrics?.incremental_orders_count || 0}</div></div>
                <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center"><div className="text-[10px] text-[var(--text-muted)]">+GMV</div><div className="text-base font-bold text-[var(--accent-emerald)]">₹{Number(step4.metrics?.incremental_revenue_inr || 0).toLocaleString()}</div></div>
              </div>
            </div>
          )}
          {step5 && (
            <div className="p-5 rounded-2xl bg-[var(--bg-card)] border border-emerald-500/30 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2"><CreditCard className="w-4 h-4 text-emerald-500" /><h2 className="font-serif text-sm font-bold">Webhook Payment Captured</h2></div>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-500">✓ Attributed</span>
              </div>
              <StepDetailRenderer stepName="payment" data={step5} />
            </div>
          )}
        </div>
      )}

      {/* TAB: REACT LOOP */}
      {activeTab === "agentic_loop" && (
        <div className="space-y-3">
          <div className="p-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] flex items-center gap-3 text-xs">
            <span className="px-2 py-0.5 rounded-full font-mono font-bold uppercase bg-amber-500/10 text-amber-500 text-[10px]">
              {agenticStepsTaken.length > 0 ? "Bounded ReAct (Max 6)" : "Deterministic Pipeline"}
            </span>
            <span className="text-[var(--text-muted)] font-mono">Provider: {step2Agentic?.provider_used || step2Det?.llm_decision?.provider_used || "nvidia_nim"}</span>
          </div>
          {agenticStepsTaken.length > 0 ? (
            agenticStepsTaken.map((st: any, idx: number) => (
              <ExpandableStepCard key={idx} stepKey={`${st.tool_name}()`} stepData={st.result} index={idx} />
            ))
          ) : (
            <div className="p-8 text-center rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] text-xs text-[var(--text-muted)]">
              No ReAct tool steps recorded. Click "Live Agentic Scan" to run.
            </div>
          )}
        </div>
      )}

      {/* TAB: VECTOR MEMORY LAB */}
      {activeTab === "vector_memory" && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-serif text-sm font-bold">ChromaDB Vector Recall & Cross-Session RAG</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-blue-500/10 text-blue-500">FastEmbed 384-Dim</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              <div className="md:col-span-2">
                <input type="text" value={ragQuery} onChange={(e) => setRagQuery(e.target.value)}
                  placeholder="Semantic query (e.g. churn prevention discount)..."
                  className="w-full px-3 py-2 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-terracotta)]" />
              </div>
              <div className="flex gap-2">
                {availableSessions.length > 0 && (
                  <select value={targetSessionId} onChange={(e) => setTargetSessionId(e.target.value)}
                    className="px-2 py-2 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-xs text-[var(--text-primary)] focus:outline-none">
                    <option value="">Compare Session...</option>
                    {availableSessions.map((s) => <option key={s.session_id} value={s.session_id}>{s.session_id} ({s.lift_display})</option>)}
                  </select>
                )}
                <button onClick={handleSearchRag} disabled={isBusy}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-[var(--accent-terracotta)] text-white text-xs font-semibold hover:opacity-90 disabled:opacity-50 cursor-pointer">
                  <Search className="w-3.5 h-3.5" />{isSearchingRag ? "Searching..." : "Vector Search"}
                </button>
              </div>
            </div>
            {comparisonNarrative && (
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs space-y-1">
                <div className="font-bold text-amber-500 flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5" /> Comparative RAG Synthesis:</div>
                <p className="text-[var(--text-primary)] leading-relaxed">{comparisonNarrative}</p>
              </div>
            )}
          </div>
          {(ragResults.length > 0 ? ragResults : memoryCitations).length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(ragResults.length > 0 ? ragResults : memoryCitations).map((res: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-emerald-500 font-mono">Memory #{idx + 1} ({res.memory_type || "campaign_outcome"})</span>
                    {res.distance !== undefined && <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/10 text-emerald-500">dist: {typeof res.distance === "number" ? res.distance.toFixed(4) : String(res.distance)}</span>}
                  </div>
                  <p className="text-[var(--text-primary)] leading-relaxed">{res.summary || res.summary_text}</p>
                  {res.metadata && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {Object.entries(res.metadata).map(([k, v]: [string, any]) => (
                        <span key={k} className="px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] text-[10px] font-mono text-[var(--text-muted)]">
                          {k}: <strong className="text-[var(--text-primary)]">{typeof v === "number" ? v.toLocaleString() : String(v)}</strong>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] text-xs text-[var(--text-muted)]">
              No memories found. Click "Vector Search" to query ChromaDB.
            </div>
          )}
        </div>
      )}

      {/* TAB: SESSION STEPS TIMELINE */}
      {activeTab === "steps" && (
        <div className="space-y-2">
          {sortedStepKeys.length > 0 ? sortedStepKeys.map((stepKey, idx) => {
            const stepObj = stepsObj[stepKey];
            const recordedAt = stepObj?.recorded_at;
            let elapsedLabel = "";
            if (idx > 0 && recordedAt && stepsObj[sortedStepKeys[idx - 1]]?.recorded_at) {
              const diff = Math.max(0, Math.round((new Date(recordedAt).getTime() - new Date(stepsObj[sortedStepKeys[idx - 1]].recorded_at).getTime()) / 1000));
              elapsedLabel = `+${diff}s`;
            }
            return <ExpandableStepCard key={stepKey} stepKey={stepKey} stepData={stepObj?.data || {}} index={idx} recordedAt={recordedAt} elapsedLabel={elapsedLabel} />;
          }) : (
            <div className="p-8 text-center rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] text-xs text-[var(--text-muted)]">No session steps found.</div>
          )}
        </div>
      )}

      {/* TAB: RAW JSON */}
      {activeTab === "raw" && (
        <pre className="p-4 rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] font-mono text-xs text-[var(--text-secondary)] overflow-x-auto whitespace-pre-wrap">
          {JSON.stringify(traceData, null, 2)}
        </pre>
      )}

      {/* Collapsible Architecture Reference with Tools & Modes */}
      <div className="border border-[var(--border-subtle)] rounded-xl overflow-hidden bg-[var(--bg-card)]">
        <button onClick={() => setShowAgentsGuide(!showAgentsGuide)}
          className="w-full p-3.5 flex items-center justify-between text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-all">
          <div className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-[var(--accent-terracotta)]" />
            <span>Architecture Reference: Domain Agents ({agentsArchitectureList.length})</span>
          </div>
          {showAgentsGuide ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        {showAgentsGuide && (
          <div className="p-4 border-t border-[var(--border-subtle)] grid grid-cols-1 md:grid-cols-2 gap-3">
            {agentsArchitectureList.map((ag, i) => {
              const Icon = ag.icon;
              return (
                <div key={i} className="p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] space-y-2">
                  <div className="flex items-center gap-2">
                    <Icon className="w-3.5 h-3.5 text-[var(--accent-terracotta)]" />
                    <span className="font-bold text-xs text-[var(--text-primary)]">{ag.name}</span>
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">({ag.role})</span>
                  </div>
                  <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">{ag.description}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {ag.tools.map((t, j) => (
                      <span key={j} className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-[var(--bg-card)] border border-[var(--border-subtle)] text-[10px] font-mono text-[var(--text-muted)]">
                        <Wrench className="w-2.5 h-2.5" />{t}
                      </span>
                    ))}
                    {ag.modes.map((m) => (
                      <span key={m} className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${m === "agentic" ? "bg-amber-500/10 text-amber-500" : "bg-blue-500/10 text-blue-500"}`}>
                        {m === "agentic" ? "ReAct" : "Pipeline"}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
