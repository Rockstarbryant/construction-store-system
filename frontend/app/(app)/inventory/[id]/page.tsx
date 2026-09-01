"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { InventoryItem, TransactionOut } from "@/lib/types";
import { useToast } from "@/lib/toast-context";
import { Button, ErrorBlock, FieldError, Input, Label, LoadingBlock, StatusText, StripedRow } from "@/components/ui";
import { formatDateTime } from "@/lib/format";

export default function InventoryItemDetailPage() {
  const params = useParams<{ id: string }>();
  const { activeSiteId, user } = useAuth();
  const { notify } = useToast();

  const [item, setItem] = useState<InventoryItem | null>(null);
  const [history, setHistory] = useState<TransactionOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showAdjust, setShowAdjust] = useState(false);
  const [delta, setDelta] = useState("");
  const [reason, setReason] = useState("");
  const [adjustError, setAdjustError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const canAdjust = user?.role === "ADMIN";

  const load = useCallback(async () => {
    if (!activeSiteId) return;
    setLoading(true);
    setError(null);
    try {
      const [i, h] = await Promise.all([
        api.get<InventoryItem>(`/inventory/${params.id}`),
        api.get<TransactionOut[]>(`/transactions?site_id=${activeSiteId}&item_id=${params.id}&limit=50`),
      ]);
      setItem(i);
      setHistory(h);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load item.");
    } finally {
      setLoading(false);
    }
  }, [activeSiteId, params.id]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleAdjust(e: FormEvent) {
    e.preventDefault();
    if (!item) return;
    setAdjustError(null);
    const deltaNum = Number(delta);
    if (!Number.isFinite(deltaNum) || deltaNum === 0) {
      setAdjustError("Enter a non-zero number (positive to add stock, negative to remove).");
      return;
    }
    if (!reason.trim()) {
      setAdjustError("A reason is required for every stock adjustment.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`/inventory/${item.id}/adjust`, { delta: deltaNum, reason });
      notify("Stock adjusted.");
      setShowAdjust(false);
      setDelta("");
      setReason("");
      await load();
    } catch (err) {
      setAdjustError(err instanceof ApiError ? err.message : "Could not adjust stock.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBlock message={error} onRetry={load} />;
  if (!item) return null;

  return (
    <div className="space-y-6">
      <section className="rounded-sm border border-line bg-panel p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-display text-xl font-semibold text-ink">{item.name}</p>
            <p className="text-sm text-ink-soft">{item.category ?? "Uncategorized"}</p>
          </div>
          <StatusText status={item.status} />
        </div>
        <div className="mt-4 grid grid-cols-3 gap-2 font-data text-center">
          <div>
            <p className="text-xl font-semibold text-ink">{item.total_quantity}</p>
            <p className="text-xs text-ink-soft">total</p>
          </div>
          <div>
            <p className="text-xl font-semibold text-moss">{item.available_quantity}</p>
            <p className="text-xs text-ink-soft">available</p>
          </div>
          <div>
            <p className="text-xl font-semibold text-amber-dark">{item.issued_quantity}</p>
            <p className="text-xs text-ink-soft">issued</p>
          </div>
        </div>

        {canAdjust && item.item_type === "CONSUMABLE" && (
          <div className="mt-4">
            {!showAdjust ? (
              <Button variant="secondary" fullWidth onClick={() => setShowAdjust(true)}>
                Adjust stock
              </Button>
            ) : (
              <form onSubmit={handleAdjust} className="space-y-3 rounded-sm border border-line bg-concrete p-3">
                <div>
                  <Label htmlFor="delta">Change (+ to add, − to remove)</Label>
                  <Input
                    id="delta"
                    type="number"
                    value={delta}
                    onChange={(e) => setDelta(e.target.value)}
                    placeholder="e.g. -5 or 20"
                  />
                </div>
                <div>
                  <Label htmlFor="reason">Reason</Label>
                  <Input
                    id="reason"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="e.g. Damaged in storage, New delivery"
                  />
                </div>
                <FieldError>{adjustError ?? undefined}</FieldError>
                <div className="flex gap-2">
                  <Button type="submit" disabled={submitting} className="flex-1">
                    Save
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setShowAdjust(false)}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            )}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-2.5 text-sm font-semibold uppercase tracking-wide text-ink-soft">
          History
        </h2>
        {history.length === 0 ? (
          <p className="py-4 text-center text-sm text-ink-soft">No transactions for this item yet.</p>
        ) : (
          <div className="space-y-1.5">
            {history.map((t) => (
              <StripedRow key={t.id} status={t.status}>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs text-ink-soft">
                      Issued {formatDateTime(t.issued_at)}
                      {t.returned_at && <> · Returned {formatDateTime(t.returned_at)}</>}
                    </p>
                  </div>
                  <StatusText status={t.status} />
                </div>
              </StripedRow>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
