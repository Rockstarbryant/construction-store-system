"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { DashboardStats } from "@/lib/types";
import { ErrorBlock, LoadingBlock, StripedRow } from "@/components/ui";
import { formatTime } from "@/lib/format";

const QUICK_ACTIONS = [
  { href: "/workers/new", label: "Register Worker", icon: "👤" },
  { href: "/transactions", label: "Issue Item", icon: "📤" },
  { href: "/transactions/outstanding", label: "Return Item", icon: "📥" },
  { href: "/workers", label: "Search Worker", icon: "🔍" },
];

function StatTile({ label, value, tone }: { label: string; value: number; tone?: "amber" | "rust" }) {
  return (
    <div className="rounded-sm border border-line bg-panel px-4 py-3">
      <p
        className={`font-data text-2xl font-semibold ${
          tone === "amber" ? "text-amber-dark" : tone === "rust" ? "text-rust" : "text-ink"
        }`}
      >
        {value}
      </p>
      <p className="mt-0.5 text-xs text-ink-soft">{label}</p>
    </div>
  );
}

export default function DashboardPage() {
  const { activeSiteId } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);

  async function load() {
    if (!activeSiteId) return;
    setLoadingStats(true);
    setError(null);
    try {
      const data = await api.get<DashboardStats>(`/dashboard?site_id=${activeSiteId}`);
      setStats(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load dashboard.");
    } finally {
      setLoadingStats(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSiteId]);

  if (!activeSiteId) return <LoadingBlock />;

  return (
    <div className="space-y-6">
      <section>
        <h2 className="mb-2.5 text-sm font-semibold uppercase tracking-wide text-ink-soft">
          Quick actions
        </h2>
        <div className="grid grid-cols-2 gap-2.5">
          {QUICK_ACTIONS.map((a) => (
            <Link
              key={a.href}
              href={a.href}
              className="flex min-h-[76px] flex-col items-center justify-center gap-1.5 rounded-sm border border-line bg-panel px-3 py-3 text-center text-sm font-semibold text-ink active:bg-concrete-dim"
            >
              <span className="text-xl" aria-hidden>
                {a.icon}
              </span>
              {a.label}
            </Link>
          ))}
        </div>
      </section>

      {loadingStats && <LoadingBlock />}
      {error && !loadingStats && <ErrorBlock message={error} onRetry={load} />}

      {stats && !loadingStats && (
        <>
          <section>
            <h2 className="mb-2.5 text-sm font-semibold uppercase tracking-wide text-ink-soft">
              Today
            </h2>
            <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
              <StatTile label="Currently issued" value={stats.items_currently_issued} tone="amber" />
              <StatTile label="Issued today" value={stats.items_issued_today} />
              <StatTile label="Returned today" value={stats.items_returned_today} />
              <StatTile label="Damaged items" value={stats.damaged_items} tone="rust" />
            </div>
          </section>

          <section>
            <h2 className="mb-2.5 text-sm font-semibold uppercase tracking-wide text-ink-soft">
              Site
            </h2>
            <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
              <StatTile label="Active workers" value={stats.active_workers} />
              <StatTile label="Total workers" value={stats.total_workers} />
              <StatTile label="Inventory items" value={stats.total_inventory_items} />
            </div>
          </section>

          <section>
            <h2 className="mb-2.5 text-sm font-semibold uppercase tracking-wide text-ink-soft">
              Recent activity
            </h2>
            {stats.recent_activity.length === 0 ? (
              <p className="py-6 text-center text-sm text-ink-soft">No activity yet today.</p>
            ) : (
              <div className="space-y-1.5">
                {stats.recent_activity.map((a, i) => (
                  <StripedRow key={i} status={a.action === "took" ? "ISSUED" : "RETURNED"}>
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm text-ink">
                        <span className="font-medium">{a.worker}</span>
                        {a.store_number && (
                          <span className="font-data text-ink-soft"> #{a.store_number}</span>
                        )}{" "}
                        {a.action} <span className="font-medium">{a.item}</span>
                      </p>
                      <span className="font-data shrink-0 text-xs text-ink-soft">
                        {formatTime(a.timestamp)}
                      </span>
                    </div>
                  </StripedRow>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
