"use client";

import React, { useState } from "react";
import { RefreshCw, FolderDown, Zap, Copy, Check, ShieldAlert, Layers } from "lucide-react";

interface HeroBannerProps {
  merchantName: string;
  merchantId: string;
  sessionId: string;
  isLoading: boolean;
  onGenerate: () => void;
  onLoadLocal: () => void;
  onRescan: () => void;
  onAgenticScan?: () => void;
}

export const HeroBanner: React.FC<HeroBannerProps> = ({
  merchantName,
  merchantId,
  sessionId,
  isLoading,
  onGenerate,
  onLoadLocal,
  onRescan,
  onAgenticScan,
}) => {
  const [copied, setCopied] = useState(false);
  const webhookUrl = typeof window !== "undefined" ? `${window.location.origin}/api/v1/webhooks/razorpay` : "/api/v1/webhooks/razorpay";

  const handleCopyWebhook = () => {
    navigator.clipboard.writeText(webhookUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full mb-6">
      {/* Main Hero Card */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-[var(--shadow-sm)] relative overflow-hidden transition-all duration-200">
        {/* Subtle Background Warm Gradient */}
        <div className="absolute -top-24 -right-24 w-72 h-72 bg-[var(--accent-terracotta)]/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-72 h-72 bg-[var(--accent-emerald)]/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          {/* Left: Text & Info */}
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-[var(--accent-terracotta-subtle)] text-[var(--accent-terracotta)] mb-3 border border-[var(--accent-terracotta-border)]">
              <Zap className="w-3 h-3" />
              <span>Track 1: AI Growth & Agentic Commerce</span>
            </div>
            <h1 className="font-serif-claude text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight text-[var(--text-primary)] leading-tight mb-2">
              Autonomous Growth Manager for Razorpay Merchants
            </h1>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              RazorGrowth AI continuously observes payment events, calculates Customer 360 RFM metrics, recalls historical campaign outcomes from RAG vector memory, decides via bounded ReAct tool loops, enforces dynamic safety guardrails, triggers live Razorpay test transactions, and measures net incremental GMV through PostgreSQL A/B experiments.
            </p>

            {/* Session Info Chips */}
            <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
              <span className="text-[var(--text-muted)]">Active Session:</span>
              <span className="font-mono-code px-2 py-0.5 rounded bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-primary)]">
                {sessionId}
              </span>
              {merchantId && (
                <span className="font-mono-code px-2 py-0.5 rounded bg-[var(--accent-blue-subtle)] border border-[var(--accent-blue-border)] text-[var(--accent-blue)]">
                  {merchantId.substring(0, 14)}
                </span>
              )}
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex flex-col sm:flex-row lg:flex-col gap-2.5 min-w-[250px]">
            {onAgenticScan && merchantId && (
              <button
                onClick={onAgenticScan}
                disabled={isLoading}
                className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-xs bg-gradient-to-r from-[var(--accent-terracotta)] to-amber-600 hover:opacity-95 text-white shadow-sm transition-all duration-150 disabled:opacity-50 cursor-pointer"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>Run Agentic Decision Scan (ReAct)</span>
              </button>
            )}

            <button
              onClick={onGenerate}
              disabled={isLoading}
              className="flex items-center justify-center gap-2 px-5 py-2 rounded-xl font-semibold text-xs bg-[var(--accent-terracotta)] hover:bg-[var(--accent-terracotta-hover)] text-white shadow-sm transition-all duration-150 disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
              <span>Generate New Session</span>
            </button>

            <button
              onClick={onLoadLocal}
              disabled={isLoading}
              className="flex items-center justify-center gap-2 px-5 py-2 rounded-xl font-semibold text-xs bg-[var(--bg-card)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] border border-[var(--border-strong)] transition-all duration-150 disabled:opacity-50 cursor-pointer"
            >
              <FolderDown className="w-3.5 h-3.5 text-[var(--accent-terracotta)]" />
              <span>Load Local JSON & Scan</span>
            </button>



            {merchantId && (
              <button
                onClick={onRescan}
                disabled={isLoading}
                className="flex items-center justify-center gap-2 px-4 py-1.5 rounded-xl text-xs font-medium bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] border border-[var(--border-subtle)] transition-all duration-150 cursor-pointer"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Deterministic 6-Stage Scan</span>
              </button>
            )}
          </div>
        </div>

        {/* ngrok Webhook Listener Banner */}
        <div className="mt-6 pt-4 border-t border-[var(--border-subtle)] flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-[var(--text-secondary)]">
            <span className="w-2 h-2 rounded-full bg-[var(--accent-emerald)]" />
            <strong className="text-[var(--text-primary)]">Live Razorpay Webhook Ingestion:</strong>
            <span className="text-[var(--text-muted)] hidden sm:inline">
              Supports live payments & ngrok forwarding with HMAC-SHA256 signature verification.
            </span>
          </div>
          <div className="flex items-center gap-2">
            <code className="font-mono-code px-2.5 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--accent-terracotta)] text-[11px]">
              /api/v1/webhooks/razorpay
            </code>
            <button
              onClick={handleCopyWebhook}
              className="p-1.5 rounded-md hover:bg-[var(--bg-card-hover)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
              title="Copy Full Webhook URL"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
