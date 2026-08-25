"use client";

import React, { useState } from "react";
import {
  Sparkles,
  ShieldCheck,
  CreditCard,
  CheckCircle2,
  Play,
  Zap,
  TrendingUp,
  AlertTriangle,
  Loader2,
  ShieldAlert,
} from "lucide-react";
import { Opportunity, ExperimentMetrics, CheckoutSession, OfferDetails, PermissionGateInfo } from "@/types";

interface OpportunityCardProps {
  opportunity: Opportunity;
  isLaunched: boolean;
  isLaunching?: boolean;
  isPaying?: boolean;
  isPendingGate?: boolean;
  pendingGate?: PermissionGateInfo | null;
  metrics?: ExperimentMetrics;
  checkoutSessions?: CheckoutSession[];
  offer?: OfferDetails;
  onLaunch: (opportunityId: string) => void;
  onConfirmSafeCap?: (opportunityId: string) => void;
  onConfirmOverride?: (opportunityId: string) => void;
  onTriggerPayment: (opportunityId: string, checkoutSession: CheckoutSession) => void;
}

export const OpportunityCard: React.FC<OpportunityCardProps> = ({
  opportunity,
  isLaunched,
  isLaunching = false,
  isPaying = false,
  isPendingGate = false,
  pendingGate = null,
  metrics,
  checkoutSessions = [],
  offer,
  onLaunch,
  onConfirmSafeCap,
  onConfirmOverride,
  onTriggerPayment,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [selectedVariant, setSelectedVariant] = useState<"treatment" | "control">("treatment");
  const checkoutSession = checkoutSessions.find((session) => session.variant === selectedVariant)
    || checkoutSessions[0];

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`bg-[var(--bg-card)] border rounded-2xl p-5 mb-4 shadow-[var(--shadow-sm)] transition-all duration-200 ${
        isLaunched
          ? "border-[var(--accent-emerald-border)] ring-1 ring-[var(--accent-emerald)]/30"
          : isPendingGate
          ? "border-amber-500/40 ring-1 ring-amber-500/20"
          : "border-[var(--border-subtle)] hover:border-[var(--border-strong)]"
      }`}
    >
      {/* Top Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[var(--accent-terracotta-subtle)] text-[var(--accent-terracotta)] flex items-center justify-center font-bold">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-serif-claude text-base sm:text-lg font-semibold text-[var(--text-primary)]">
              {opportunity.title}
            </h3>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[11px] text-[var(--text-muted)] capitalize">
                Segment: <strong>{opportunity.target_segment || "Target Cohort"}</strong>
              </span>
              <span className="text-[var(--text-dim)]">•</span>
              <span className="text-[11px] text-[var(--text-muted)] font-mono-code">
                {opportunity.audience_count} candidates
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="badge-claude badge-terracotta text-[11px]">
            Confidence: {Math.round(opportunity.confidence * 100)}%
          </span>
          <div className="text-right">
            <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-semibold">
              Est. Opportunity
            </div>
            <div className="font-serif-claude text-base font-bold text-[var(--accent-terracotta)]">
              ₹{Math.round(opportunity.estimated_gmv).toLocaleString("en-IN")}
            </div>
          </div>
        </div>
      </div>

      {/* Description */}
      <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-4">
        {opportunity.description}
      </p>

      {/* Inline Permission Gate Required Notice (When safety threshold is hit for this card) */}
      {isPendingGate && !isLaunched && (
        <div className="mb-4 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 animate-in fade-in">
          <div className="flex items-start gap-2.5 mb-2.5">
            <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div>
              <div className="text-xs font-semibold text-amber-700 dark:text-amber-300">
                Permission Gate Review Required
              </div>
              <p className="text-[11px] text-amber-800/80 dark:text-amber-200/80 mt-0.5 leading-relaxed">
                {pendingGate?.policy_notes || "Audience size or discount depth exceeds automated safety policy."}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-amber-500/20">
            <button
              onClick={() => onConfirmSafeCap?.(opportunity.id)}
              disabled={isLaunching}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-all cursor-pointer disabled:opacity-50"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Launch with Safe Cap (Recommended)</span>
            </button>
            <button
              onClick={() => onConfirmOverride?.(opportunity.id)}
              disabled={isLaunching}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-600 hover:bg-amber-700 text-white shadow-sm transition-all cursor-pointer disabled:opacity-50"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Override Guardrail & Launch Full Audience</span>
            </button>
          </div>
        </div>
      )}

      {/* Footer / Launch Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-[var(--border-subtle)]">
        <div className="text-xs text-[var(--text-muted)] flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-[var(--accent-emerald)]" />
          <span>Dynamic safety verified via Permission Gate</span>
        </div>

        <div>
          {isLaunched ? (
            <div className="badge-claude badge-emerald text-xs py-1.5 px-3">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>[ACTIVE] Action Deployed & Seeded</span>
            </div>
          ) : (
            <button
              onClick={() => onLaunch(opportunity.id)}
              disabled={isLaunching || isPendingGate}
              className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--accent-terracotta)] hover:bg-[var(--accent-terracotta-hover)] text-white shadow-sm transition-all duration-150 cursor-pointer w-full sm:w-auto disabled:opacity-50"
            >
              {isLaunching ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Evaluating & Launching...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Launch Autonomous Action</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Inline Dedicated A/B Experiment Workbench (When Launched) */}
      {isLaunched && (
        <div className="mt-4 pt-4 border-t border-[var(--border-subtle)] bg-[var(--bg-secondary)]/70 rounded-xl p-4 animate-fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-[var(--accent-emerald)]" />
              <span className="font-semibold text-xs text-[var(--text-primary)]">
                A/B Experiment Benchmark (80% Treatment / 20% Control)
              </span>
            </div>
            <span className="badge-claude badge-emerald text-[10px]">
              MEASURED VIA RAZORPAY TEST MODE
            </span>
          </div>

          {/* Metrics Comparison Table */}
          <div className="overflow-x-auto mb-3">
            <table className="w-full text-left text-xs border-collapse font-mono-code">
              <thead>
                <tr className="border-b border-[var(--border-subtle)] text-[var(--text-muted)] text-[11px]">
                  <th className="py-2 px-2 font-medium font-sans">Cohort Variant</th>
                  <th className="py-2 px-2 text-right">Assigned</th>
                  <th className="py-2 px-2 text-right">Orders</th>
                  <th className="py-2 px-2 text-right">Conversion Rate</th>
                  <th className="py-2 px-2 text-right">GMV (₹)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)] text-[var(--text-primary)]">
                <tr>
                  <td className="py-2 px-2 font-sans font-medium text-[var(--text-secondary)]">
                    Control Group (Organic Baseline)
                  </td>
                  <td className="py-2 px-2 text-right">
                    {metrics ? metrics.control_customers_count : Math.round(opportunity.audience_count * 0.2)}
                  </td>
                  <td className="py-2 px-2 text-right">
                    {metrics ? metrics.control_orders_count : 0}
                  </td>
                  <td className="py-2 px-2 text-right">
                    {metrics ? `${(metrics.control_conversion_rate * 100).toFixed(1)}%` : "0.0%"}
                  </td>
                  <td className="py-2 px-2 text-right">₹0</td>
                </tr>
                <tr className="bg-[var(--accent-emerald-subtle)]/30 font-semibold">
                  <td className="py-2 px-2 font-sans text-[var(--accent-emerald)] flex items-center gap-1.5">
                    <span>Treatment Group (Personalized Offer)</span>
                    {offer && (
                      <span className="font-mono-code text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-card)] border border-[var(--accent-emerald-border)] text-[var(--accent-emerald)]">
                        {offer.offer_code}
                      </span>
                    )}
                  </td>
                  <td className="py-2 px-2 text-right text-[var(--accent-emerald)]">
                    {metrics ? metrics.treatment_customers_count : Math.round(opportunity.audience_count * 0.8)}
                  </td>
                  <td className="py-2 px-2 text-right text-[var(--accent-emerald)] font-bold">
                    {metrics ? metrics.treatment_orders_count : 0}
                  </td>
                  <td className="py-2 px-2 text-right text-[var(--accent-emerald)] font-bold">
                    {metrics ? `${(metrics.treatment_conversion_rate * 100).toFixed(1)}%` : "0.0%"}
                  </td>
                  <td className="py-2 px-2 text-right text-[var(--accent-emerald)] font-bold">
                    ₹{metrics ? Math.round(metrics.incremental_revenue_inr).toLocaleString("en-IN") : "0"}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Statistical Lift Summary Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3 text-center">
            <div className="p-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)]">
              <div className="text-[10px] text-[var(--text-muted)]">Absolute Diff</div>
              <div className="font-mono-code font-bold text-xs text-[var(--accent-blue)]">
                {metrics ? `+${metrics.absolute_difference_percentage.toFixed(2)} pp` : "+0.00 pp"}
              </div>
            </div>
            <div className="p-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)]">
              <div className="text-[10px] text-[var(--text-muted)]">Relative Lift</div>
              <div className="font-mono-code font-bold text-xs text-[var(--accent-terracotta)]">
                {metrics ? metrics.relative_lift_display : "N/A"}
              </div>
            </div>
            <div className="p-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)]">
              <div className="text-[10px] text-[var(--text-muted)]">Incremental Orders</div>
              <div className="font-mono-code font-bold text-xs text-[var(--accent-emerald)]">
                {metrics ? `+${metrics.incremental_orders_count}` : "+0"}
              </div>
            </div>
            <div className="p-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)]">
              <div className="text-[10px] text-[var(--text-muted)]">Net Lift GMV</div>
              <div className="font-serif-claude font-bold text-sm text-[var(--accent-emerald)]">
                ₹{metrics ? Math.round(metrics.incremental_revenue_inr).toLocaleString("en-IN") : "0"}
              </div>
            </div>
          </div>

          {/* Live Razorpay Test Order Simulation Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-[var(--bg-card)] rounded-xl border border-[var(--border-subtle)]">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-[var(--accent-blue-subtle)] text-[var(--accent-blue)]">
                <CreditCard className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[var(--text-primary)]">
                  Live Razorpay Test Order Seeded
                </div>
                <select
                  aria-label="Experiment cohort"
                  value={selectedVariant}
                  onChange={(event) => setSelectedVariant(event.target.value as "treatment" | "control")}
                  className="mt-1 w-full rounded border border-[var(--border-subtle)] bg-[var(--bg-secondary)] px-2 py-1 text-[10px] text-[var(--text-secondary)]"
                >
                  <option value="treatment">Treatment checkout (offer)</option>
                  <option value="control">Control checkout (normal price)</option>
                </select>
                <div className="text-[11px] text-[var(--text-muted)] font-mono-code">
                  {checkoutSession
                    ? `Order: ${checkoutSession.razorpay_order_id} (${checkoutSession.customer_name || "Customer"} - ₹${checkoutSession.amount.toLocaleString("en-IN")})`
                    : "Ready for live webhook conversion"}
                </div>
              </div>
            </div>

            <button
              onClick={() => checkoutSession && onTriggerPayment(opportunity.id, checkoutSession)}
              disabled={isPaying || !checkoutSession}
              className="flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--accent-emerald)] hover:bg-emerald-700 text-white shadow-sm transition-all duration-150 cursor-pointer w-full sm:w-auto disabled:opacity-50"
            >
              {isPaying ? (
                <><Loader2 className="w-3.5 h-3.5 animate-spin" /><span>Verifying Payment...</span></>
              ) : (
                <><Play className="w-3.5 h-3.5 fill-current" /><span>Record {selectedVariant} Test Payment</span></>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
