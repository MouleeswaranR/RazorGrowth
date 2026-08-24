"use client";

import React from "react";
import { ShieldAlert, CheckCircle2, AlertTriangle, X } from "lucide-react";
import { PermissionGateInfo } from "@/types";

interface PermissionGateBannerProps {
  permissionGate: PermissionGateInfo | null;
  opportunityTitle?: string;
  eligibleAudience: number;
  safeAudienceCap: number;
  onConfirmSafeCap: () => void;
  onConfirmFullOverride: () => void;
  onDismiss: () => void;
}

export const PermissionGateBanner: React.FC<PermissionGateBannerProps> = ({
  permissionGate,
  opportunityTitle,
  eligibleAudience,
  safeAudienceCap,
  onConfirmSafeCap,
  onConfirmFullOverride,
  onDismiss,
}) => {
  if (!permissionGate) return null;

  return (
    <div className="w-full bg-[var(--accent-amber-subtle)] border border-[var(--accent-amber-border)] rounded-2xl p-5 mb-6 shadow-md animate-fade-in">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-xl bg-amber-500/20 text-amber-600 dark:text-amber-400 mt-0.5">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-serif-claude text-base font-semibold text-[var(--text-primary)]">
                Dynamic Permission Gate Guardrail Notice
              </h3>
              <span className="badge-claude badge-amber text-[10px]">
                REQUIRES MERCHANT APPROVAL
              </span>
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-1 leading-relaxed max-w-2xl">
              {permissionGate.policy_notes ||
                "This campaign target size or discount budget exceeds automatic risk parameters calculated from current store GMV."}
            </p>

            <div className="mt-3 flex flex-wrap items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="text-[var(--text-muted)]">Target Opportunity:</span>
                <strong className="text-[var(--text-primary)] font-medium">
                  {opportunityTitle || "Growth Campaign"}
                </strong>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[var(--text-muted)]">Eligible Cohort:</span>
                <strong className="text-[var(--text-primary)] font-mono-code">
                  {eligibleAudience} customers
                </strong>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[var(--text-muted)]">Auto-Approved Safe Cap:</span>
                <strong className="text-[var(--accent-emerald)] font-mono-code">
                  {safeAudienceCap} customers
                </strong>
              </div>
            </div>
          </div>
        </div>

        <button
          onClick={onDismiss}
          className="p-1.5 rounded-lg hover:bg-[var(--bg-card)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Decision Actions */}
      <div className="mt-4 pt-4 border-t border-[var(--accent-amber-border)]/50 flex flex-wrap items-center gap-3">
        <button
          onClick={onConfirmSafeCap}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--accent-emerald)] hover:bg-emerald-700 text-white shadow-sm transition-all duration-150 cursor-pointer"
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Option A: Cap to Top {safeAudienceCap} High-Value Customers (Recommended)</span>
        </button>

        <button
          onClick={onConfirmFullOverride}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-amber-600 hover:bg-amber-700 text-white shadow-sm transition-all duration-150 cursor-pointer"
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>Option B: Authorize Full {eligibleAudience} Customers (Override Guardrail)</span>
        </button>

        <button
          onClick={onDismiss}
          className="px-3 py-2 rounded-xl text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card)] transition-colors cursor-pointer"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};
