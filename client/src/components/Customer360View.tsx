"use client";

import React, { useState, useMemo } from "react";
import {
  Users,
  Search,
  Filter,
  PieChart,
  ShieldAlert,
  CreditCard,
  ArrowUpDown,
  ExternalLink,
} from "lucide-react";
import { Customer } from "@/types";

interface Customer360ViewProps {
  customers: Customer[];
  merchantName: string;
}

export const Customer360View: React.FC<Customer360ViewProps> = ({
  customers,
  merchantName,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSegment, setSelectedSegment] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  // Segment Breakdown Aggregation
  const segmentStats = useMemo(() => {
    const map: Record<string, { count: number; spend: number }> = {};
    customers.forEach((c) => {
      const seg = c.segment || "Unclassified";
      if (!map[seg]) map[seg] = { count: 0, spend: 0 };
      map[seg].count += 1;
      map[seg].spend += c.total_spend || 0;
    });
    return map;
  }, [customers]);

  // Churn Risk Tiers
  const churnTiers = useMemo(() => {
    let high = 0;
    let medium = 0;
    let low = 0;
    customers.forEach((c) => {
      const score = c.churn_risk || 0;
      if (score >= 0.6) high++;
      else if (score >= 0.3) medium++;
      else low++;
    });
    return { high, medium, low };
  }, [customers]);

  // Filtered Customers
  const filteredCustomers = useMemo(() => {
    return customers.filter((c) => {
      const matchesSearch =
        c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (c.location && c.location.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesSegment =
        selectedSegment === "all" || c.segment === selectedSegment;
      return matchesSearch && matchesSegment;
    });
  }, [customers, searchQuery, selectedSegment]);

  const totalPages = Math.ceil(filteredCustomers.length / pageSize) || 1;
  const paginatedCustomers = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredCustomers.slice(start, start + pageSize);
  }, [filteredCustomers, currentPage]);

  const segmentsList = ["all", ...Object.keys(segmentStats)];

  return (
    <div className="w-full space-y-6">
      {/* Top Intelligence Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Segment Distribution */}
        <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)]">
          <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-semibold uppercase tracking-wider mb-3">
            <span>RFM Behavioral Segments</span>
            <PieChart className="w-4 h-4 text-[var(--accent-terracotta)]" />
          </div>
          <div className="space-y-2.5">
            {Object.entries(segmentStats).slice(0, 4).map(([seg, data]) => {
              const pct = customers.length > 0 ? (data.count / customers.length) * 100 : 0;
              return (
                <div key={seg}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-[var(--text-primary)] font-medium">{seg}</span>
                    <span className="font-mono-code text-[var(--text-muted)]">
                      {data.count} ({pct.toFixed(0)}%)
                    </span>
                  </div>
                  <div className="w-full bg-[var(--bg-secondary)] rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-[var(--accent-terracotta)] h-full rounded-full transition-all duration-300"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Card 2: Churn Risk Health */}
        <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)]">
          <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-semibold uppercase tracking-wider mb-3">
            <span>Churn Risk Profile</span>
            <ShieldAlert className="w-4 h-4 text-rose-500" />
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400">
              <span>High Churn Risk (&ge; 60%)</span>
              <strong className="font-mono-code text-sm font-bold">{churnTiers.high}</strong>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400">
              <span>Moderate Risk (30% - 59%)</span>
              <strong className="font-mono-code text-sm font-bold">{churnTiers.medium}</strong>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400">
              <span>Healthy Active (&lt; 30%)</span>
              <strong className="font-mono-code text-sm font-bold">{churnTiers.low}</strong>
            </div>
          </div>
        </div>

        {/* Card 3: Payment Method Health (Razorpay Intelligence) */}
        <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)]">
          <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-semibold uppercase tracking-wider mb-3">
            <span>Payment Method Benchmarks</span>
            <CreditCard className="w-4 h-4 text-[var(--accent-blue)]" />
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-primary)] font-medium">UPI / Instant Intent</span>
              <span className="font-mono-code text-emerald-600 dark:text-emerald-400 font-semibold">
                94.8% Success
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-primary)] font-medium">Credit / Debit Cards</span>
              <span className="font-mono-code text-blue-600 dark:text-blue-400 font-semibold">
                88.2% Success
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-primary)] font-medium">Netbanking</span>
              <span className="font-mono-code text-amber-600 dark:text-amber-400 font-semibold">
                79.4% (Drop-off alert)
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-primary)] font-medium">Wallets & Pay Later</span>
              <span className="font-mono-code text-emerald-600 dark:text-emerald-400 font-semibold">
                84.1% Success
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Search & Filter Table Panel */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-4 border-b border-[var(--border-subtle)]">
          <div>
            <h3 className="font-serif-claude text-lg font-semibold text-[var(--text-primary)]">
              Customer 360 Unified Ledger
            </h3>
            <p className="text-xs text-[var(--text-muted)]">
              Showing {filteredCustomers.length} enriched profiles for {merchantName || "merchant"}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search Input */}
            <div className="relative min-w-[200px]">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder="Search name, email, city..."
                className="w-full pl-9 pr-3 py-1.5 rounded-xl text-xs bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-terracotta)] placeholder:text-[var(--text-muted)]"
              />
            </div>

            {/* Segment Filter */}
            <div className="flex items-center gap-1.5 text-xs">
              <Filter className="w-3.5 h-3.5 text-[var(--text-muted)]" />
              <select
                value={selectedSegment}
                onChange={(e) => {
                  setSelectedSegment(e.target.value);
                  setCurrentPage(1);
                }}
                className="py-1.5 px-2.5 rounded-xl text-xs bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-terracotta)] capitalize"
              >
                {segmentsList.map((seg) => (
                  <option key={seg} value={seg}>
                    {seg === "all" ? "All Segments" : seg}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Customer Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse font-mono-code">
            <thead>
              <tr className="border-b border-[var(--border-subtle)] text-[var(--text-muted)] text-[11px] font-sans">
                <th className="py-2.5 px-3 font-medium">Customer</th>
                <th className="py-2.5 px-3 font-medium">Location</th>
                <th className="py-2.5 px-3 font-medium">Segment</th>
                <th className="py-2.5 px-3 font-medium text-right">Orders</th>
                <th className="py-2.5 px-3 font-medium text-right">Total Spend (₹)</th>
                <th className="py-2.5 px-3 font-medium text-right">Churn Risk</th>
                <th className="py-2.5 px-3 font-medium text-right">12-Mo CLV (₹)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-subtle)] text-[var(--text-primary)]">
              {paginatedCustomers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[var(--text-muted)] font-sans text-xs">
                    No customers match the current filter or search criteria.
                  </td>
                </tr>
              ) : (
                paginatedCustomers.map((c) => {
                  const isHighChurn = (c.churn_risk || 0) >= 0.6;
                  const isLowChurn = (c.churn_risk || 0) < 0.3;

                  return (
                    <tr
                      key={c.id}
                      className="hover:bg-[var(--bg-secondary)]/50 transition-colors"
                    >
                      <td className="py-2.5 px-3 font-sans">
                        <div className="font-semibold text-[var(--text-primary)]">{c.name}</div>
                        <div className="text-[11px] text-[var(--text-muted)] font-mono-code">{c.email}</div>
                      </td>
                      <td className="py-2.5 px-3 font-sans text-[var(--text-secondary)]">
                        {c.location || "—"}
                      </td>
                      <td className="py-2.5 px-3 font-sans">
                        <span className="badge-claude badge-terracotta text-[10px]">
                          {c.segment}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right text-[var(--text-primary)]">
                        {c.total_orders}
                      </td>
                      <td className="py-2.5 px-3 text-right font-medium">
                        ₹{Number(c.total_spend || 0).toLocaleString("en-IN")}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <span
                          className={`font-semibold ${
                            isHighChurn
                              ? "text-rose-500"
                              : isLowChurn
                              ? "text-emerald-500"
                              : "text-amber-500"
                          }`}
                        >
                          {((c.churn_risk || 0) * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right text-[var(--accent-emerald)] font-bold">
                        ₹{Number(c.clv || 0).toLocaleString("en-IN")}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between pt-4 mt-3 border-t border-[var(--border-subtle)] text-xs text-[var(--text-muted)] font-sans">
            <div>
              Page {currentPage} of {totalPages} ({filteredCustomers.length} total)
            </div>
            <div className="flex items-center gap-1.5">
              <button
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1 rounded-lg border border-[var(--border-subtle)] disabled:opacity-40 hover:bg-[var(--bg-secondary)] cursor-pointer"
              >
                Previous
              </button>
              <button
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                className="px-3 py-1 rounded-lg border border-[var(--border-subtle)] disabled:opacity-40 hover:bg-[var(--bg-secondary)] cursor-pointer"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
