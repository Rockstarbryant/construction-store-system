"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { DailyReport, InventoryReportLine } from "@/lib/types";
import { ErrorBlock, LoadingBlock } from "@/components/ui";

export default function ReportsPage() {
  const { activeSiteId } = useAuth();
  const [daily, setDaily] = useState<DailyReport | null>(null);
  const [inventory, setInventory] = useState<InventoryReportLine[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!activeSiteId) return;
    setLoading(true);
    setError(null);
    try {
      const [d, inv] = await Promise.all([
        api.get<DailyReport>(`/reports/daily?site_id=${activeSiteId}`),
        api.get<InventoryReportLine[]>(`/reports/inventory?site_id=${activeSiteId}`),
      ]);
      setDaily(d);
      setInventory(inv);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load reports.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSiteId]);

  function downloadCsv() {
    if (!inventory) return;
    const header = "Item,Total,Available,Issued,Damaged";
    const rows = inventory.map((r) => `${r.item},${r.total},${r.available},${r.issued},${r.damaged}`);
    const csv = [header, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `inventory-report-${daily?.date ?? "today"}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBlock message={error} onRetry={load} />;

  return (
    <div className="space-y-6">
      {daily && (
        <section>
          <h2 className="mb-2.5 text-sm font-semibold uppercase tracking-wide text-ink-soft">
            Daily report — {daily.date}
          </h2>
          <div className="grid grid-cols-2 gap-2.5">
            <div className="rounded-sm border border-line bg-panel px-4 py-3">
              <p className="font-data text-2xl font-semibold text-ink">{daily.workers_served}</p>
              <p className="text-xs text-ink-soft">workers served</p>
            </div>
            <div className="rounded-sm border border-line bg-panel px-4 py-3">
              <p className="font-data text-2xl font-semibold text-ink">{daily.items_issued}</p>
              <p className="text-xs text-ink-soft">items issued</p>
            </div>
            <div className="rounded-sm border border-line bg-panel px-4 py-3">
              <p className="font-data text-2xl font-semibold text-ink">{daily.items_returned}</p>
              <p className="text-xs text-ink-soft">items returned</p>
            </div>
            <div className="rounded-sm border border-line bg-panel px-4 py-3">
              <p className="font-data text-2xl font-semibold text-amber-dark">
                {daily.currently_outstanding}
              </p>
              <p className="text-xs text-ink-soft">outstanding</p>
            </div>
          </div>
        </section>
      )}

      {inventory && (
        <section>
          <div className="mb-2.5 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-soft">
              Inventory report
            </h2>
            <button onClick={downloadCsv} className="text-sm font-medium text-steel underline">
              Export CSV
            </button>
          </div>
          <div className="overflow-x-auto rounded-sm border border-line">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line bg-panel text-left text-ink-soft">
                  <th className="px-3 py-2 font-medium">Item</th>
                  <th className="px-3 py-2 text-right font-medium">Total</th>
                  <th className="px-3 py-2 text-right font-medium">Avail.</th>
                  <th className="px-3 py-2 text-right font-medium">Issued</th>
                  <th className="px-3 py-2 text-right font-medium">Damaged</th>
                </tr>
              </thead>
              <tbody className="font-data">
                {inventory.map((r) => (
                  <tr key={r.item} className="border-b border-line last:border-0">
                    <td className="px-3 py-2 font-sans">{r.item}</td>
                    <td className="px-3 py-2 text-right">{r.total}</td>
                    <td className="px-3 py-2 text-right text-moss">{r.available}</td>
                    <td className="px-3 py-2 text-right text-amber-dark">{r.issued}</td>
                    <td className="px-3 py-2 text-right text-rust">{r.damaged}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
