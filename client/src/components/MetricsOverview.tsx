"use client";

import React from "react";
import { Users, TrendingUp, ShieldCheck, CheckCircle2 } from "lucide-react";

interface MetricsOverviewProps {
  customerCount: number;
  orderCount: number;
  opportunityGmv: number;
  opportunityCount: number;
  measuredGmvLift: number;
  incrementalOrdersCount: number;
  permissionGateStatus: string;
}

export const MetricsOverview: React.FC<MetricsOverviewProps> = ({
  customerCount,
  orderCount,
  opportunityGmv,
  opportunityCount,
  measuredGmvLift,
  incrementalOrdersCount,
  permissionGateStatus,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Metric 1: Customers & Orders */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-[var(--shadow-sm)] hover:border-[var(--border-strong)] transition-all duration-200">
        <div className="flex items-center justify-between text-xs text-[var(--text-muted)] uppercase tracking-wider font-semibold mb-2">
          <span>Customer 360 Base</span>
          <Users className="w-4 h-4 text-[var(--accent-blue)]" />
        </div>
        <div className="font-serif-claude text-2xl sm:text-3xl font-bold text-[var(--text-primary)] mb-1">
          {customerCount.toLocaleString()}
        </div>
        <div className="text-xs text-[var(--text-secondary)] flex items-center gap-1.5">
          <span className="font-mono-code font-medium text-[var(--text-primary)]">
            {orderCount.toLocaleString()}
          </span>
          <span>orders analyzed</span>
        </div>
      </div>

      {/* Metric 2: Detected Opportunity GMV */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-[var(--shadow-sm)] hover:border-[var(--border-strong)] transition-all duration-200">
        <div className="flex items-center justify-between text-xs text-[var(--text-muted)] uppercase tracking-wider font-semibold mb-2">
          <span>Opportunity Pipeline</span>
          <TrendingUp className="w-4 h-4 text-[var(--accent-terracotta)]" />
        </div>
        <div className="font-serif-claude text-2xl sm:text-3xl font-bold text-[var(--accent-terracotta)] mb-1">
          ₹{Math.round(opportunityGmv).toLocaleString("en-IN")}
        </div>
        <div className="text-xs text-[var(--text-secondary)] flex items-center gap-1.5">
          <span className="font-mono-code font-medium text-[var(--text-primary)]">
            {opportunityCount}
          </span>
          <span>autonomous opportunities found</span>
        </div>
      </div>

      {/* Metric 3: Safety Guardrails */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-[var(--shadow-sm)] hover:border-[var(--border-strong)] transition-all duration-200">
        <div className="flex items-center justify-between text-xs text-[var(--text-muted)] uppercase tracking-wider font-semibold mb-2">
          <span>Permission Gate</span>
          <ShieldCheck className="w-4 h-4 text-[var(--accent-amber)]" />
        </div>
        <div className="font-serif-claude text-2xl sm:text-3xl font-bold text-[var(--text-primary)] mb-1 capitalize">
          {permissionGateStatus || "Active"}
        </div>
        <div className="text-xs text-[var(--text-secondary)] flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-emerald)]" />
          <span>Dynamic Store GMV Thresholds</span>
        </div>
      </div>

      {/* Metric 4: Measured Incremental GMV Lift */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-[var(--shadow-sm)] hover:border-[var(--border-strong)] transition-all duration-200 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-24 bg-[var(--accent-emerald)]/5 rounded-bl-full pointer-events-none" />
        <div className="flex items-center justify-between text-xs text-[var(--text-muted)] uppercase tracking-wider font-semibold mb-2">
          <span>Measured Net Lift</span>
          <CheckCircle2 className="w-4 h-4 text-[var(--accent-emerald)]" />
        </div>
        <div className="font-serif-claude text-2xl sm:text-3xl font-bold text-[var(--accent-emerald)] mb-1">
          +₹{Math.round(measuredGmvLift).toLocaleString("en-IN")}
        </div>
        <div className="text-xs text-[var(--text-secondary)] flex items-center gap-1.5">
          <span className="font-mono-code font-semibold text-[var(--accent-emerald)]">
            +{incrementalOrdersCount}
          </span>
          <span>incremental orders in PostgreSQL</span>
        </div>
      </div>
    </div>
  );
};
