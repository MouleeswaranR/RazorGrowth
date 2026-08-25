"use client";

import React, { useState, useEffect } from "react";
import {
  Webhook,
  Radio,
  Send,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";
import { getRecentWebhooks, simulateWebhookEvent } from "@/services/api";
import { WebhookEventRecord } from "@/types";

interface WebhookLabViewProps {
  sessionId: string;
  onPaymentTriggered?: () => void;
}

export const WebhookLabView: React.FC<WebhookLabViewProps> = ({
  sessionId,
  onPaymentTriggered,
}) => {
  const [webhooks, setWebhooks] = useState<WebhookEventRecord[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [simCampaignId, setSimCampaignId] = useState<string>("cmp_demo");
  const [simCustomerId, setSimCustomerId] = useState<string>("cust_001");
  const [simAmount, setSimAmount] = useState<number>(2850);
  const [simVariant, setSimVariant] = useState<"treatment" | "control">("treatment");
  const [simResult, setSimResult] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const fetchWebhooks = async () => {
    setIsLoading(true);
    try {
      const res = await getRecentWebhooks();
      setWebhooks(res.events || []);
      setTotalCount(res.total || 0);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWebhooks();
    const interval = setInterval(fetchWebhooks, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulate = async () => {
    try {
      const res = await simulateWebhookEvent(
        simCampaignId,
        simCustomerId,
        simAmount,
        sessionId,
        simVariant,
      );
      setSimResult(res);
      fetchWebhooks();
      onPaymentTriggered?.();
    } catch (e: any) {
      alert(`Simulation error: ${e.message}`);
    }
  };

  const handleCopyWebhookUrl = () => {
    const url = `${window.location.origin}/api/v1/webhooks/razorpay`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full space-y-6">
      {/* Top Banner & ngrok Integration Guide */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)]">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-[var(--border-subtle)]">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Webhook className="w-5 h-5 text-[var(--accent-emerald)]" />
              <h3 className="font-serif-claude text-lg font-semibold text-[var(--text-primary)]">
                Live Razorpay Webhook Ingestion & Signature Verification
              </h3>
            </div>
            <p className="text-xs text-[var(--text-muted)]">
              Receives, verifies HMAC-SHA256 signatures, persists to PostgreSQL{" "}
              <code className="font-mono-code text-[var(--accent-terracotta)]">webhook_events</code>, and triggers real-time A/B conversion recalculation.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="badge-claude badge-emerald">
              <Radio className="w-3 h-3 text-[var(--accent-emerald)]" />
              <span>Listener Active</span>
            </div>
            <button
              onClick={fetchWebhooks}
              className="p-2 rounded-xl border border-[var(--border-subtle)] hover:bg-[var(--bg-secondary)] text-[var(--text-secondary)] transition-colors cursor-pointer"
              title="Refresh webhook logs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* ngrok Quick Setup Instructions */}
        <div className="mt-4 p-4 rounded-xl bg-[var(--bg-secondary)]/70 border border-[var(--border-subtle)] text-xs space-y-2">
          <div className="flex items-center justify-between">
            <strong className="text-[var(--text-primary)] font-medium">
              Local ngrok Tunnel URL for Razorpay Test Webhooks:
            </strong>
            <button
              onClick={handleCopyWebhookUrl}
              className="flex items-center gap-1 text-[var(--accent-terracotta)] hover:underline cursor-pointer"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? "Copied" : "Copy Endpoint"}</span>
            </button>
          </div>
          <div className="font-mono-code bg-[var(--bg-card)] p-2 rounded-lg border border-[var(--border-subtle)] text-[var(--text-primary)] overflow-x-auto">
            POST /api/v1/webhooks/razorpay &nbsp;&nbsp;(Secret: set in .env RAZORPAY_WEBHOOK_SECRET)
          </div>
          <p className="text-[11px] text-[var(--text-muted)]">
            Configure this URL inside the Razorpay Dashboard &rarr; Settings &rarr; Webhooks with event <code>payment.captured</code> and <code>order.paid</code>.
          </p>
        </div>
      </div>

      {/* Grid: Simulator Tool & Recent Event Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Interactive Webhook Simulator */}
        <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)] space-y-4">
          <div>
            <h4 className="font-serif-claude text-base font-semibold text-[var(--text-primary)] mb-1">
              Interactive Webhook Simulator
            </h4>
            <p className="text-xs text-[var(--text-muted)]">
              Simulate an authentic Razorpay <code className="font-mono-code">payment.captured</code> webhook event to test instant conversion and lift recalculation.
            </p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-[var(--text-muted)] mb-1 font-medium">
                Cohort Variant
              </label>
              <select
                value={simVariant}
                onChange={(event) => setSimVariant(event.target.value as "treatment" | "control")}
                className="w-full px-3 py-2 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[var(--accent-terracotta)]"
              >
                <option value="treatment">Treatment (offer checkout)</option>
                <option value="control">Control (normal checkout)</option>
              </select>
            </div>

            <div>
              <label className="block text-[var(--text-muted)] mb-1 font-medium">
                Campaign ID (matches experiment assignment)
              </label>
              <input
                type="text"
                value={simCampaignId}
                onChange={(e) => setSimCampaignId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-primary)] font-mono-code text-xs focus:outline-none focus:border-[var(--accent-terracotta)]"
              />
            </div>

            <div>
              <label className="block text-[var(--text-muted)] mb-1 font-medium">
                Customer ID
              </label>
              <input
                type="text"
                value={simCustomerId}
                onChange={(e) => setSimCustomerId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-primary)] font-mono-code text-xs focus:outline-none focus:border-[var(--accent-terracotta)]"
              />
            </div>

            <div>
              <label className="block text-[var(--text-muted)] mb-1 font-medium">
                Captured Amount (INR ₹)
              </label>
              <input
                type="number"
                value={simAmount}
                onChange={(e) => setSimAmount(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-primary)] font-mono-code text-xs focus:outline-none focus:border-[var(--accent-terracotta)]"
              />
            </div>

            <button
              onClick={handleSimulate}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl font-semibold text-xs bg-[var(--accent-terracotta)] hover:bg-[var(--accent-terracotta-hover)] text-white shadow-sm transition-all duration-150 cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Simulate Webhook Delivery</span>
            </button>
          </div>

          {simResult && (
            <div className="mt-3 p-3 rounded-xl bg-[var(--accent-emerald-subtle)] border border-[var(--accent-emerald-border)] text-xs text-[var(--accent-emerald)] space-y-1 animate-fade-in">
              <div className="flex items-center gap-1.5 font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Simulated Webhook Successfully Processed!</span>
              </div>
              <p className="text-[11px] text-[var(--text-secondary)] font-mono-code">
                Payment: {simResult.event?.payment_id || "pay_simulated"} | Status: Converted in PostgreSQL
              </p>
            </div>
          )}
        </div>

        {/* Right: Live Webhook Event Log Buffer */}
        <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)] space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-serif-claude text-base font-semibold text-[var(--text-primary)] mb-1">
                Recent Ingested Webhooks ({totalCount})
              </h4>
              <p className="text-xs text-[var(--text-muted)]">
                Real-time stream of parsed Razorpay payloads
              </p>
            </div>
          </div>

          <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
            {webhooks.length === 0 ? (
              <div className="py-12 text-center text-xs text-[var(--text-muted)]">
                No webhook events received yet. Simulate one or trigger a test order.
              </div>
            ) : (
              webhooks.map((ev, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-secondary)]/60 text-xs space-y-1.5 font-mono-code"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-[var(--accent-emerald)]">
                      {ev.event || "payment.captured"}
                    </span>
                    <span className="badge-claude badge-blue text-[9px]">
                      {ev.method || "upi"}
                    </span>
                  </div>
                  <div className="text-[11px] text-[var(--text-secondary)]">
                    Payment ID: <strong className="text-[var(--text-primary)]">{ev.payment_id || "pay_..."}</strong>
                  </div>
                  <div className="text-[11px] text-[var(--text-secondary)] flex items-center justify-between">
                    <span>Order: {ev.order_id || "order_..."}</span>
                    <span className="text-[var(--accent-emerald)] font-bold">
                      ₹{ev.amount ? Number(ev.amount).toLocaleString("en-IN") : "2,850"}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
