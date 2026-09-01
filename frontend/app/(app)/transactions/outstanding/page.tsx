"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { ItemCondition, TransactionOut } from "@/lib/types";
import { useToast } from "@/lib/toast-context";
import { Button, EmptyState, ErrorBlock, Input, LoadingBlock, Select, StripedRow } from "@/components/ui";
import { formatDateTime, formatDuration } from "@/lib/format";

const CONDITIONS: ItemCondition[] = ["GOOD", "FAIR", "DAMAGED", "NEEDS_REPAIR", "LOST"];

export default function OutstandingItemsPage() {
  const { activeSiteId, user } = useAuth();
  const { notify } = useToast();
  const searchParams = useSearchParams();
  const workerFilter = searchParams.get("worker_id");

  const [items, setItems] = useState<TransactionOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterText, setFilterText] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [conditions, setConditions] = useState<Record<string, ItemCondition>>({});
  const [returning, setReturning] = useState(false);

  const canWrite = user?.role === "ADMIN" || user?.role === "STOREKEEPER";

  const load = useCallback(async () => {
    if (!activeSiteId) return;
    setLoading(true);
    setError(null);
    try {
      const url = workerFilter
        ? `/transactions/outstanding?site_id=${activeSiteId}&worker_id=${workerFilter}`
        : `/transactions/outstanding?site_id=${activeSiteId}`;
      const data = await api.get<TransactionOut[]>(url);
      // longest-outstanding first
      setItems([...data].sort((a, b) => new Date(a.issued_at).getTime() - new Date(b.issued_at).getTime()));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load outstanding items.");
    } finally {
      setLoading(false);
    }
  }, [activeSiteId, workerFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = items.filter(
    (t) =>
      !filterText.trim() ||
      t.inventory_item_name.toLowerCase().includes(filterText.trim().toLowerCase()) ||
      t.worker_full_name.toLowerCase().includes(filterText.trim().toLowerCase())
  );

  function toggleSelect(id: string) {
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function returnSelected() {
    if (selected.size === 0) return;
    setReturning(true);
    try {
      await api.post("/transactions/return", {
        items: Array.from(selected).map((id) => ({
          transaction_id: id,
          condition_on_return: conditions[id] ?? "GOOD",
        })),
      });
      notify(`${selected.size} item(s) returned.`);
      setSelected(new Set());
      await load();
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not return items.", "error");
    } finally {
      setReturning(false);
    }
  }

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBlock message={error} onRetry={load} />;

  return (
    <div className="space-y-4">
      <Input
        placeholder="Filter by worker or item name"
        value={filterText}
        onChange={(e) => setFilterText(e.target.value)}
      />

      {filtered.length === 0 ? (
        <EmptyState
          title="No outstanding items"
          description="All issued equipment has been returned."
        />
      ) : (
        <>
          <div className="space-y-1.5">
            {filtered.map((t) => (
              <StripedRow key={t.id} status="ISSUED">
                <div className="flex items-start gap-3">
                  {canWrite && (
                    <input
                      type="checkbox"
                      className="mt-1.5 h-5 w-5 shrink-0 accent-ink"
                      checked={selected.has(t.id)}
                      onChange={() => toggleSelect(t.id)}
                      aria-label={`Select ${t.inventory_item_name}`}
                    />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-ink">{t.inventory_item_name}</p>
                    <p className="font-data text-xs text-ink-soft">
                      {t.worker_full_name} · #{t.worker_store_number}
                    </p>
                    <p className="text-xs text-ink-soft">
                      Issued {formatDateTime(t.issued_at)} · out {formatDuration(t.issued_at)}
                    </p>
                  </div>
                </div>
                {canWrite && selected.has(t.id) && (
                  <Select
                    className="mt-2.5 min-h-[40px] text-sm"
                    value={conditions[t.id] ?? "GOOD"}
                    onChange={(e) =>
                      setConditions((c) => ({ ...c, [t.id]: e.target.value as ItemCondition }))
                    }
                  >
                    {CONDITIONS.map((c) => (
                      <option key={c} value={c}>
                        {c.replace("_", " ")}
                      </option>
                    ))}
                  </Select>
                )}
              </StripedRow>
            ))}
          </div>

          {canWrite && selected.size > 0 && (
            <div className="sticky bottom-16 z-20">
              <Button fullWidth onClick={returnSelected} disabled={returning}>
                {returning ? "Returning…" : `Return selected (${selected.size})`}
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
