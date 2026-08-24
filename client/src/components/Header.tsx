import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Sparkles, Moon, Sun, ShieldCheck, Play, Radio, Terminal, Activity } from "lucide-react";
import { SessionSwitcher } from "@/components/SessionSwitcher";

interface HeaderProps {
  merchantName: string;
  sessionId: string;
  onSelectSession?: (sessionId: string) => void;
  onStartDemoTour: () => void;
  onOpenTerminal: () => void;
  isTerminalOpen: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  merchantName,
  sessionId,
  onSelectSession,
  onStartDemoTour,
  onOpenTerminal,
  isTerminalOpen,
}) => {
  const [isDark, setIsDark] = useState<boolean>(false);

  useEffect(() => {
    // Check initial system or saved theme preference
    const saved = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    if (saved === "dark" || (!saved && prefersDark)) {
      setIsDark(true);
      document.documentElement.classList.add("dark");
    } else {
      setIsDark(false);
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const toggleTheme = () => {
    if (isDark) {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
      setIsDark(false);
    } else {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
      setIsDark(true);
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full backdrop-blur-md bg-[var(--bg-card)]/85 border-b border-[var(--border-subtle)] transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Logo & Brand */}
        <Link href="/" className="flex items-center gap-2.5 group cursor-pointer">
          <div className="w-8 h-8 rounded-xl bg-[var(--accent-terracotta)] text-white flex items-center justify-center shadow-xs transition-transform group-hover:scale-105">
            <span className="font-serif-claude text-lg font-bold italic leading-none">R</span>
          </div>
          <span className="font-serif-claude text-xl font-bold tracking-tight text-[var(--text-primary)]">
            RazorGrowth AI
          </span>
        </Link>

        {/* Center Status Badges */}
        <div className="hidden md:flex items-center gap-3">
          <div className="badge-claude badge-emerald">
            <span className="w-2 h-2 rounded-full bg-[var(--accent-emerald)] animate-pulse-glow" />
            <span>Razorpay Sandbox Connected</span>
          </div>
          <div className="badge-claude badge-blue">
            <Radio className="w-3 h-3 text-[var(--accent-blue)]" />
            <span className="font-mono-code text-[11px]">
              {merchantName ? `${merchantName}` : "Awaiting Data"}
            </span>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Session Switcher & History Dropdown */}
          <SessionSwitcher
            currentSessionId={sessionId}
            onSelectSession={onSelectSession || (() => {})}
          />



          {/* Quick 1-Click Demo Tour */}
          <button
            onClick={onStartDemoTour}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--accent-terracotta)] hover:bg-[var(--accent-terracotta-hover)] text-white shadow-sm transition-all duration-150 cursor-pointer"
            title="Start automated 7-step Hackathon presentation demo flow"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">1-Click Demo Run</span>
            <span className="sm:hidden">Demo</span>
          </button>

          {/* Terminal Toggle */}
          <button
            onClick={onOpenTerminal}
            className={`p-2 rounded-lg border text-xs font-medium transition-colors cursor-pointer ${
              isTerminalOpen
                ? "bg-[var(--accent-terracotta-subtle)] border-[var(--accent-terracotta-border)] text-[var(--accent-terracotta)]"
                : "border-[var(--border-subtle)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)]"
            }`}
            title="Toggle Live Event & Telemetry Logs"
          >
            <Terminal className="w-4 h-4" />
          </button>

          {/* Dark / Light Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg border border-[var(--border-subtle)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] transition-colors cursor-pointer"
            title={isDark ? "Switch to Warm Sand Light Theme" : "Switch to Dark Obsidian Theme"}
          >
            {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </header>
  );
};
