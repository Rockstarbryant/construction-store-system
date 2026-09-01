"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { ItemCondition, TransactionOut, Worker } from "@/lib/types";
import { useToast } from "@/lib/toast-context";
import {
  Button,
  ErrorBlock,
  LoadingBlock,
  Select,
  StatusText,
  StripedRow,
} from "@/components/ui";
import { formatDateTime, formatDuration } from "@/lib/format";

const CONDITIONS: ItemCondition[] = ["GOOD", "FAIR", "DAMAGED", "NEEDS_REPAIR", "LOST"];

export default function WorkerProfilePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { activeSiteId, user } = useAuth();
  const { notify } = useToast();

  const [worker, setWorker] = useState<Worker | null>(null);
  const [outstanding, setOutstanding] = useState<TransactionOut[]>([]);
  const [history, setHistory] = useState<TransactionOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [returningIds, setReturningIds] = useState<Set<string>>(new Set());
  const [conditions, setConditions] = useState<Record<string, ItemCondition>>({});

  const canWrite = user?.role === "ADMIN" || user?.role === "STOREKEEPER";

  const load = useCallback(async () => {
    if (!activeSiteId) return;
    setLoading(true);
    setError(null);
    try {
      const [w, out, hist] = await Promise.all([
        api.get<Worker>(`/workers/${params.id}`),
        api.get<TransactionOut[]>(`/transactions/outstanding?site_id=${activeSiteId}&worker_id=${params.id}`),
        api.get<TransactionOut[]>(`/transactions?site_id=${activeSiteId}&worker_id=${params.id}&limit=50`),
      ]);
      setWorker(w);
      setOutstanding(out);
      setHistory(hist);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load worker.");
    } finally {
      setLoading(false);
    }
  }, [activeSiteId, params.id]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleReturn(txnId: string) {
    setReturningIds((s) => new Set(s).add(txnId));
    try {
      await api.post("/transactions/return", {
        items: [{ transaction_id: txnId, condition_on_return: conditions[txnId] ?? "GOOD" }],
      });
      notify("Item returned.");
      await load();
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not return item.", "error");
    } finally {
      setReturningIds((s) => {
        const next = new Set(s);
        next.delete(txnId);
        return next;
      });
    }
  }

  async function toggleStatus() {
    if (!worker) return;
    const nextStatus = worker.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
    try {
      const updated = await api.patch<Worker>(`/workers/${worker.id}`, { status: nextStatus });
      setWorker(updated);
      notify(`Worker marked ${nextStatus.toLowerCase()}.`);
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not update worker.", "error");
    }
  }

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBlock message={error} onRetry={load} />;
  if (!worker) return null;

  return (
    <div className="space-y-6">
      <section className="rounded-sm border border-line bg-panel p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-display text-xl font-semibold text-ink">{worker.full_name}</p>
            <p className="font-data text-2xl font-bold text-ink">#{worker.store_number}</p>
          </div>
          <StatusText status={worker.status} />
        </div>
        <dl className="mt-3 space-y-1 text-sm text-ink-soft">
          <div className="flex justify-between">
            <dt>Phone</dt>
            <dd className="font-data text-ink">{worker.phone_number}</dd>
          </div>
          <div className="flex justify-between">
            <dt>National ID</dt>
            <dd className="font-data text-ink">{worker.national_id_masked}</dd>
          </div>
          {worker.job_role && (
            <div className="flex justify-between">
              <dt>Role</dt>
              <dd className="text-ink">{worker.job_role}</dd>
            </div>
          )}
          {worker.supervisor && (
            <div className="flex justify-between">
              <dt>Supervisor</dt>
              <dd className="text-ink">{worker.supervisor}</dd>
            </div>
          )}
        </dl>
        {canWrite && (
          <Button variant="secondary" className="mt-4" onClick={toggleStatus}>
            {worker.status === "ACTIVE" ? "Mark inactive" : "Reactivate worker"}
          </Button>
        )}
      </section>

      <section>
        <div className="mb-2.5 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-soft">
            Currently holding
          </h2>
          {outstanding.length > 0 && canWrite && (
            <Button
              onClick={() =>
                router.push(`/transactions/outstanding?worker_id=${worker.id}`)
              }
              variant="ghost"
              className="min-h-0 px-2 py-1 text-xs"
            >
              Return all →
            </Button>
          )}
        </div>
        {outstanding.length === 0 ? (
          <p className="py-4 text-center text-sm text-ink-soft">
            All items returned. Nothing currently issued.
          </p>
        ) : (
          <div className="space-y-1.5">
            {outstanding.map((t) => (
              <StripedRow key={t.id} status="ISSUED">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-ink">{t.inventory_item_name}</p>
                    <p className="text-xs text-ink-soft">
                      Issued {formatDateTime(t.issued_at)} · out {formatDuration(t.issued_at)}
                    </p>
                  </div>
                </div>
                {canWrite && (
                  <div className="mt-2.5 flex items-center gap-2">
                    <Select
                      className="min-h-[40px] flex-1 text-sm"
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
                    <Button
                      onClick={() => handleReturn(t.id)}
                      disabled={returningIds.has(t.id)}
                      className="min-h-[40px] px-4 py-2 text-sm"
                    >
                      {returningIds.has(t.id) ? "…" : "Return"}
                    </Button>
                  </div>
                )}
              </StripedRow>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-2.5 text-sm font-semibold uppercase tracking-wide text-ink-soft">
          Transaction history
        </h2>
        {history.length === 0 ? (
          <p className="py-4 text-center text-sm text-ink-soft">No transactions yet.</p>
        ) : (
          <div className="space-y-1.5">
            {history.map((t) => (
              <StripedRow key={t.id} status={t.status}>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-ink">
                      {t.inventory_item_name}
                      {t.quantity > 1 && <span className="text-ink-soft"> ×{t.quantity}</span>}
                    </p>
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
