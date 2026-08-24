"use client";

import React, { useRef, useEffect } from "react";
import { Terminal, X, Trash2 } from "lucide-react";

interface TerminalDrawerProps {
  isOpen: boolean;
  logs: string[];
  onClose: () => void;
  onClear: () => void;
}

export const TerminalDrawer: React.FC<TerminalDrawerProps> = ({
  isOpen,
  logs,
  onClose,
  onClear,
}) => {
  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 bg-[var(--bg-card)] border-t border-[var(--border-subtle)] shadow-2xl p-4 transition-all duration-200">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-[var(--border-subtle)] text-xs">
          <div className="flex items-center gap-2 text-[var(--text-primary)] font-semibold">
            <Terminal className="w-4 h-4 text-[var(--accent-terracotta)]" />
            <span>Live Telemetry & Execution Log Console</span>
            <span className="badge-claude badge-blue text-[10px]">
              {logs.length} events
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClear}
              className="p-1 rounded hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
              title="Clear logs"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="font-mono-code text-[11px] bg-[var(--bg-secondary)] p-3 rounded-xl border border-[var(--border-subtle)] max-h-44 overflow-y-auto space-y-1 text-[var(--text-secondary)]">
          {logs.map((log, index) => (
            <div key={index} className="leading-relaxed">
              {log}
            </div>
          ))}
          <div ref={terminalEndRef} />
        </div>
      </div>
    </div>
  );
};
