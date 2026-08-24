"use client";

import React, { useState } from "react";
import {
  Sparkles,
  X,
  Play,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Database,
  Brain,
  Search,
  ShieldCheck,
  Send,
  Webhook,
  TrendingUp,
} from "lucide-react";

interface QuickTourModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRunStep: (stepNumber: number) => Promise<void>;
}

export const QuickTourModal: React.FC<QuickTourModalProps> = ({
  isOpen,
  onClose,
  onRunStep,
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isRunning, setIsRunning] = useState(false);

  if (!isOpen) return null;

  const steps = [
    {
      number: 1,
      title: "Generate Merchant Dataset & Ingest Telemetry",
      icon: Database,
      tag: "OBSERVE",
      endpoint: "POST /api/v1/simulator/generate",
      description:
        "Generates 500 customer profiles and 2,000 order transactions over a 90-day window for StyleKart. Seeds specific behavioral patterns such as VIP Dormancy (>5,000 INR spend, inactive >30 days).",
    },
    {
      number: 2,
      title: "Inspect Customer 360 & Intelligence Layer",
      icon: Brain,
      tag: "UNDERSTAND",
      endpoint: "GET /api/v1/customers",
      description:
        "Calculates unified customer profiles with computed RFM segments, 3-factor churn risk scores, and 12-month predictive CLV estimates.",
    },
    {
      number: 3,
      title: "Trigger Autonomous Growth Scan",
      icon: Search,
      tag: "OPPORTUNITY",
      endpoint: "POST /api/v1/growth/scan/{merchant_id}",
      description:
        "GrowthManagerAgent discovers high-ROI revenue leakages: Dormant VIP Recovery, Payment Method Drop-offs below 92%, and High-AOV Cross-Sell Affinities.",
    },
    {
      number: 4,
      title: "Evaluate Dynamic Permission Gate Guardrails",
      icon: ShieldCheck,
      tag: "DECIDE",
      endpoint: "PermissionGateService (Internal Policy)",
      description:
        "Evaluates merchant risk parameters against total store GMV. Automatically approves safe actions or prompts Option A (Safe Audience Cap) vs Option B (Merchant Override).",
    },
    {
      number: 5,
      title: "Launch Autonomous Campaign & Razorpay Test Orders",
      icon: Send,
      tag: "ACT",
      endpoint: "POST /api/v1/campaigns/launch/{opportunity_id}",
      description:
        "ExperimentAgent splits cohort into 80% Treatment and 20% Control. Calls Razorpay API in test mode to create real order IDs (order_...) with structured metadata notes.",
    },
    {
      number: 6,
      title: "Ingest Live Razorpay Payment Webhooks",
      icon: Webhook,
      tag: "CAPTURE",
      endpoint: "POST /api/v1/webhooks/razorpay",
      description:
        "Captures authentic payment.captured webhook events with HMAC-SHA256 signature verification, recording customer conversions directly into PostgreSQL.",
    },
    {
      number: 7,
      title: "Quantify True Incremental GMV & Lift",
      icon: TrendingUp,
      tag: "MEASURE",
      endpoint: "GET /api/v1/experiments/results/{campaign_id}",
      description:
        "Recalculates conversion rates, absolute percentage points difference, and net incremental revenue against counterfactual control baseline. Marked 'MEASURED VIA RAZORPAY TEST MODE'.",
    },
  ];

  const step = steps[currentStep - 1];
  const StepIcon = step.icon;

  const handleExecuteCurrentStep = async () => {
    setIsRunning(true);
    try {
      await onRunStep(currentStep);
      if (currentStep < 7) {
        setCurrentStep((prev) => prev + 1);
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-3xl max-w-xl w-full p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        {/* Top Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-[var(--accent-terracotta)] text-white flex items-center justify-center font-bold">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-serif-claude text-lg font-semibold text-[var(--text-primary)]">
                Hackathon Presentation Demonstration Flow
              </h3>
              <p className="text-xs text-[var(--text-muted)]">
                7-Step Autonomous Commerce Judging Walkthrough
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Step Progress Tracker */}
        <div className="my-5 flex items-center justify-between gap-1">
          {steps.map((st) => (
            <button
              key={st.number}
              onClick={() => setCurrentStep(st.number)}
              className={`flex-1 h-2 rounded-full transition-all duration-200 cursor-pointer ${
                st.number === currentStep
                  ? "bg-[var(--accent-terracotta)]"
                  : st.number < currentStep
                  ? "bg-[var(--accent-emerald)]"
                  : "bg-[var(--bg-secondary)]"
              }`}
              title={`Step ${st.number}: ${st.title}`}
            />
          ))}
        </div>

        {/* Step Content Box */}
        <div className="bg-[var(--bg-secondary)]/70 border border-[var(--border-subtle)] rounded-2xl p-5 mb-6 space-y-3">
          <div className="flex items-center justify-between">
            <span className="badge-claude badge-terracotta text-[10px]">
              {step.tag} • STEP {step.number} OF 7
            </span>
            <span className="font-mono-code text-[11px] text-[var(--text-muted)]">
              {step.endpoint}
            </span>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-[var(--bg-card)] text-[var(--accent-terracotta)] border border-[var(--border-subtle)] shrink-0">
              <StepIcon className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-serif-claude text-base font-semibold text-[var(--text-primary)]">
                {step.title}
              </h4>
              <p className="text-xs text-[var(--text-secondary)] mt-1 leading-relaxed">
                {step.description}
              </p>
            </div>
          </div>
        </div>

        {/* Modal Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
          <div className="flex items-center gap-2">
            <button
              disabled={currentStep <= 1 || isRunning}
              onClick={() => setCurrentStep((prev) => Math.max(1, prev - 1))}
              className="px-3 py-2 rounded-xl text-xs font-semibold border border-[var(--border-subtle)] hover:bg-[var(--bg-secondary)] text-[var(--text-secondary)] disabled:opacity-40 transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5 inline mr-1" />
              Previous
            </button>
            <button
              disabled={currentStep >= 7 || isRunning}
              onClick={() => setCurrentStep((prev) => Math.min(7, prev + 1))}
              className="px-3 py-2 rounded-xl text-xs font-semibold border border-[var(--border-subtle)] hover:bg-[var(--bg-secondary)] text-[var(--text-secondary)] disabled:opacity-40 transition-colors cursor-pointer"
            >
              Next
              <ArrowRight className="w-3.5 h-3.5 inline ml-1" />
            </button>
          </div>

          <button
            onClick={handleExecuteCurrentStep}
            disabled={isRunning}
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-[var(--accent-terracotta)] hover:bg-[var(--accent-terracotta-hover)] text-white shadow-sm transition-all duration-150 cursor-pointer disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 fill-current ${isRunning ? "animate-spin" : ""}`} />
            <span>{isRunning ? "Executing Step..." : `Run Step ${currentStep} Live`}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
