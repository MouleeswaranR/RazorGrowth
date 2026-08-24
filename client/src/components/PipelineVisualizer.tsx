"use client";

import React from "react";
import { Eye, Brain, Search, ShieldCheck, Send, BarChart3, ChevronRight } from "lucide-react";

interface PipelineVisualizerProps {
  currentStage: number; // 1 to 6
  onSelectStage?: (stage: number) => void;
}

export const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({
  currentStage,
  onSelectStage,
}) => {
  const stages = [
    {
      id: 1,
      title: "1. Observe",
      subtitle: "Razorpay Telemetry",
      icon: Eye,
      description: "Ingests payment events, refunds, orders, and customer transaction logs.",
    },
    {
      id: 2,
      title: "2. Understand",
      subtitle: "Customer 360 & RFM",
      icon: Brain,
      description: "Computes 3-factor churn risk, 12-mo CLV, and behavioral cohort segments.",
    },
    {
      id: 3,
      title: "3. Opportunity",
      subtitle: "Autonomous Detection",
      icon: Search,
      description: "Detects dormant VIPs, drop-off payment methods, and cross-sell affinities.",
    },
    {
      id: 4,
      title: "4. Decide",
      subtitle: "Permission Gate",
      icon: ShieldCheck,
      description: "Enforces dynamic financial guardrails, safe audience caps, and auto-approvals.",
    },
    {
      id: 5,
      title: "5. Act",
      subtitle: "Multi-Agent Dispatch",
      icon: Send,
      description: "Deploys targeted incentives and creates live Razorpay test orders.",
    },
    {
      id: 6,
      title: "6. Measure",
      subtitle: "PostgreSQL A/B Lift",
      icon: BarChart3,
      description: "Tracks HMAC webhooks and recalculates true incremental GMV lift.",
    },
  ];

  return (
    <div className="w-full bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 mb-6 shadow-[var(--shadow-sm)]">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-[var(--border-subtle)]">
        <div>
          <h2 className="font-serif-claude text-base sm:text-lg font-semibold text-[var(--text-primary)]">
            Autonomous Growth Loop Architecture
          </h2>
          <p className="text-xs text-[var(--text-muted)]">
            Closed-loop intelligence: from transaction observation to mathematically measured revenue lift.
          </p>
        </div>
        <div className="text-[11px] font-mono-code text-[var(--text-secondary)]">
          Stage {currentStage} of 6
        </div>
      </div>

      {/* Grid of Steps */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {stages.map((st) => {
          const Icon = st.icon;
          const isActive = st.id === currentStage;
          const isPassed = st.id < currentStage;

          return (
            <button
              key={st.id}
              onClick={() => onSelectStage?.(st.id)}
              className={`text-left p-3.5 rounded-xl border transition-all duration-150 flex flex-col justify-between cursor-pointer ${
                isActive
                  ? "bg-[var(--accent-terracotta-subtle)] border-[var(--accent-terracotta-border)] shadow-sm ring-1 ring-[var(--accent-terracotta)]"
                  : isPassed
                  ? "bg-[var(--bg-secondary)] border-[var(--border-subtle)] hover:bg-[var(--bg-card-hover)] opacity-90"
                  : "bg-[var(--bg-card)] border-[var(--border-subtle)] hover:bg-[var(--bg-card-hover)] opacity-70"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                      isActive
                        ? "bg-[var(--accent-terracotta)] text-white"
                        : isPassed
                        ? "bg-[var(--accent-emerald-subtle)] text-[var(--accent-emerald)]"
                        : "bg-[var(--bg-secondary)] text-[var(--text-muted)]"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  {isPassed && (
                    <span className="text-[10px] font-mono-code text-[var(--accent-emerald)] font-bold">
                      ✓ DONE
                    </span>
                  )}
                </div>

                <div className="font-semibold text-xs text-[var(--text-primary)]">
                  {st.title}
                </div>
                <div className="text-[11px] text-[var(--accent-terracotta)] font-medium">
                  {st.subtitle}
                </div>
              </div>

              <div className="mt-2 text-[10px] text-[var(--text-muted)] leading-tight line-clamp-2">
                {st.description}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
