"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  History,
  ChevronDown,
  RefreshCw,
  GitCompare,
  TrendingUp,
  Sparkles,
  CheckCircle2,
  X,
  Layers,
  Brain,
  ArrowRight,
} from "lucide-react";
import { listSessions, crossReferenceSessions } from "@/services/api";
import { SessionSummary, CrossReferenceResult } from "@/types";

interface SessionSwitcherProps {
  currentSessionId: string;
  onSelectSession: (sessionId: string) => void;
  onCrossReferenceChat?: (query: string) => void;
}

export const SessionSwitcher: React.FC<SessionSwitcherProps> = ({
  currentSessionId,
  onSelectSession,
  onCrossReferenceChat,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [comparingSession, setComparingSession] = useState<SessionSummary | null>(null);
  const [comparisonResult, setComparisonResult] = useState<CrossReferenceResult | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchSessions = async () => {
    setIsLoading(true);
    try {
      const res = await listSessions();
      if (res && res.sessions) {
        setSessions(res.sessions);
      }
    } catch (e) {
      console.error("Failed to load sessions:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [currentSessionId]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleCrossReference = async (targetSession: SessionSummary) => {
    setComparingSession(targetSession);
    setIsComparing(true);
    try {
      const res = await crossReferenceSessions(
        currentSessionId,
        targetSession.session_id,
        `Compare conversion lift and offer strategies between current session ${currentSessionId} and benchmark session ${targetSession.session_id}.`
      );
      setComparisonResult(res);
    } catch (e) {
      console.error("Comparison error:", e);
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) fetchSessions();
        }}
        className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] border border-[var(--border-subtle)] hover:border-[var(--border-strong)] transition-all cursor-pointer shadow-2xs"
      >
        <History className="w-3.5 h-3.5 text-[var(--accent-terracotta)]" />
        <span className="font-mono text-[11px] text-[var(--text-muted)]">Session:</span>
        <span className="font-mono font-bold text-[var(--text-primary)] max-w-[110px] truncate">
          {currentSessionId}
        </span>
        <ChevronDown className={`w-3.5 h-3.5 text-[var(--text-muted)] transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-subtle)] shadow-[var(--shadow-md)] p-3 z-50 animate-in fade-in zoom-in-95">
          <div className="flex items-center justify-between pb-2.5 mb-2 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-[var(--accent-terracotta)]" />
              <span className="font-semibold text-xs text-[var(--text-primary)]">
                Session History & Cross-Reference
              </span>
            </div>
            <button
              onClick={fetchSessions}
              disabled={isLoading}
              className="p-1 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
              title="Refresh session list"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            </button>
          </div>

          {/* Session List */}
          <div className="max-h-64 overflow-y-auto space-y-1.5 pr-1">
            {sessions.length === 0 ? (
              <div className="py-6 text-center text-xs text-[var(--text-muted)]">
                No previous sessions recorded yet. Run a growth scan to save session memories!
              </div>
            ) : (
              sessions.map((sess) => {
                const isCurrent = sess.session_id === currentSessionId;

                return (
                  <div
                    key={sess.session_id}
                    className={`p-2.5 rounded-xl border transition-all text-xs ${
                      isCurrent
                        ? "bg-[var(--accent-terracotta-subtle)]/40 border-[var(--accent-terracotta-border)]"
                        : "bg-[var(--bg-secondary)]/50 hover:bg-[var(--bg-secondary)] border-[var(--border-subtle)]"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-1.5">
                        <span className={`w-2 h-2 rounded-full ${isCurrent ? "bg-[var(--accent-terracotta)]" : "bg-gray-400"}`} />
                        <span className="font-mono font-semibold text-[var(--text-primary)] text-[11px]">
                          {sess.session_id}
                        </span>
                        {isCurrent && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[var(--accent-terracotta)] text-white">
                            ACTIVE
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-[var(--text-muted)] font-mono" suppressHydrationWarning>
                        {sess.last_updated
                          ? new Date(sess.last_updated.endsWith("Z") || sess.last_updated.includes("+") ? sess.last_updated : `${sess.last_updated}Z`).toLocaleTimeString("en-IN", {
                              timeZone: "Asia/Kolkata",
                              hour: "2-digit",
                              minute: "2-digit",
                              hour12: true,
                            })
                          : "Recent"}
                      </span>
                    </div>

                    <div className="text-[11px] text-[var(--text-secondary)] truncate mb-2">
                      {sess.top_opportunity}
                    </div>

                    <div className="flex items-center justify-between pt-1 border-t border-black/5 dark:border-white/5 text-[10px]">
                      <div className="flex items-center gap-2 text-[var(--text-muted)]">
                        {sess.has_experiment ? (
                          <span className="text-[var(--accent-emerald)] font-semibold flex items-center gap-1">
                            <TrendingUp className="w-3 h-3" />
                            Lift: {sess.lift_display}
                          </span>
                        ) : (
                          <span>Scanned ({sess.total_audience || 50} audience)</span>
                        )}
                      </div>

                      <div className="flex items-center gap-1.5">
                        {!isCurrent && (
                          <button
                            onClick={() => {
                              onSelectSession(sess.session_id);
                              setIsOpen(false);
                            }}
                            className="px-2 py-0.5 rounded-md bg-[var(--bg-card)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] border border-[var(--border-subtle)] font-medium cursor-pointer transition-colors"
                          >
                            Switch
                          </button>
                        )}
                        <button
                          onClick={() => handleCrossReference(sess)}
                          className="px-2 py-0.5 rounded-md bg-[var(--accent-terracotta)] hover:bg-[var(--accent-terracotta-hover)] text-white font-medium flex items-center gap-1 cursor-pointer transition-colors shadow-xs"
                          title="Cross-reference with this session using RAG Vector Memory"
                        >
                          <GitCompare className="w-2.5 h-2.5" />
                          <span>Cross-Ref</span>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Cross-Reference Comparative Modal */}
      {comparingSession && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto shadow-2xl p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[var(--accent-terracotta)] text-white flex items-center justify-center font-bold">
                  <GitCompare className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-serif text-base font-semibold text-[var(--text-primary)]">
                    Cross-Session Comparative Analysis (RAG)
                  </h3>
                  <p className="text-[11px] text-[var(--text-muted)]">
                    Active: <strong className="font-mono text-[var(--accent-terracotta)]">{currentSessionId}</strong> vs Benchmark: <strong className="font-mono text-blue-500">{comparingSession.session_id}</strong>
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  setComparingSession(null);
                  setComparisonResult(null);
                }}
                className="p-1 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {isComparing ? (
              <div className="py-12 text-center space-y-3">
                <div className="w-8 h-8 border-2 border-[var(--accent-terracotta)] border-t-transparent rounded-full animate-spin mx-auto" />
                <div className="text-xs font-semibold text-[var(--text-primary)]">
                  Synthesizing Cross-Session Vector Memories...
                </div>
                <p className="text-[11px] text-[var(--text-muted)] max-w-sm mx-auto">
                  Querying ChromaDB 384-dimensional dense vectors and trace logs to benchmark conversion lifts and offer effectiveness.
                </p>
              </div>
            ) : comparisonResult ? (
              <div className="space-y-4 text-xs animate-in fade-in">
                {/* AI Comparative Diagnosis Narrative */}
                <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] leading-relaxed">
                  <div className="flex items-center gap-2 font-semibold text-[var(--accent-terracotta)] mb-2">
                    <Brain className="w-4 h-4" />
                    <span>Cross-Session AI Diagnosis:</span>
                  </div>
                  <div className="text-[var(--text-primary)] whitespace-pre-wrap leading-relaxed">
                    {comparisonResult.comparison_narrative}
                  </div>
                </div>

                {/* Side-by-Side Metrics Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3.5 rounded-xl bg-[var(--bg-card)] border border-[var(--accent-terracotta-border)] shadow-xs">
                    <div className="text-[11px] font-bold text-[var(--accent-terracotta)] mb-2 font-mono">
                      Current Session ({currentSessionId})
                    </div>
                    <div className="space-y-1.5 text-[11px] text-[var(--text-secondary)]">
                      <div>Opportunity: <strong>{comparisonResult.current_metrics?.opportunity_title || "Active Scan"}</strong></div>
                      <div>Conversion Rate: <strong>{comparisonResult.current_metrics?.treatment_conversion_rate || "0.0%"}</strong></div>
                      <div>Incremental GMV: <strong>{comparisonResult.current_metrics?.incremental_gmv_inr || "₹0.00"}</strong></div>
                      <div>Relative Lift: <strong>{comparisonResult.current_metrics?.relative_conversion_lift || "N/A"}</strong></div>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[var(--bg-card)] border border-blue-500/30 shadow-xs">
                    <div className="text-[11px] font-bold text-blue-600 dark:text-blue-400 mb-2 font-mono">
                      Benchmark Session ({comparingSession.session_id})
                    </div>
                    <div className="space-y-1.5 text-[11px] text-[var(--text-secondary)]">
                      <div>Opportunity: <strong>{comparingSession.top_opportunity}</strong></div>
                      <div>Conversion Rate: <strong>{comparisonResult.target_metrics?.treatment_conversion_rate || "0.0%"}</strong></div>
                      <div>Incremental GMV: <strong>{comparisonResult.target_metrics?.incremental_gmv_inr || "₹0.00"}</strong></div>
                      <div>Relative Lift: <strong>{comparingSession.lift_display}</strong></div>
                    </div>
                  </div>
                </div>

                {/* Vector Memory Citations */}
                {comparisonResult.vector_memories && comparisonResult.vector_memories.length > 0 && (
                  <div className="p-3.5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)]">
                    <div className="text-[11px] font-semibold text-[var(--text-primary)] mb-2 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-[var(--accent-emerald)]" />
                      <span>Retrieved Vector Memories from ChromaDB:</span>
                    </div>
                    <div className="space-y-1.5">
                      {comparisonResult.vector_memories.map((mem, idx) => (
                        <div key={idx} className="p-2 rounded-lg bg-[var(--bg-secondary)] text-[10px] font-mono text-[var(--text-secondary)] border border-[var(--border-subtle)]">
                          {mem.summary}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : null}

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-[var(--border-subtle)]">
              <button
                onClick={() => {
                  setComparingSession(null);
                  setComparisonResult(null);
                }}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] border border-[var(--border-subtle)] cursor-pointer transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
