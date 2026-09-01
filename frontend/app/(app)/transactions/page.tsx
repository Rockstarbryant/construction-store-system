"use client";

import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { InventoryItem, TransactionOut, Worker, WorkerSearchResult } from "@/lib/types";
import { useToast } from "@/lib/toast-context";
import { Button, Input, LoadingBlock, Select } from "@/components/ui";

interface CartLine {
  item: InventoryItem;
  quantity: number;
}

export default function IssueItemsPage() {
  const { activeSiteId } = useAuth();
  const { notify } = useToast();

  // worker search
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<WorkerSearchResult[]>([]);
  const [selectedWorker, setSelectedWorker] = useState<Worker | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // inventory + cart
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [cart, setCart] = useState<CartLine[]>([]);
  const [pickItemId, setPickItemId] = useState("");
  const [pickQty, setPickQty] = useState("1");

  const [issuing, setIssuing] = useState(false);
  const [lastIssued, setLastIssued] = useState<TransactionOut[] | null>(null);

  useEffect(() => {
    if (!activeSiteId) return;
    api
      .get<InventoryItem[]>(`/inventory?site_id=${activeSiteId}`)
      .then((data) => setItems(data.filter((i) => i.item_type === "CONSUMABLE")))
      .catch(() => setItems([]));
  }, [activeSiteId]);

  useEffect(() => {
    if (!activeSiteId || selectedWorker) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.trim().length === 0) {
      setResults([]);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await api.get<WorkerSearchResult[]>(
          `/workers/search?site_id=${activeSiteId}&q=${encodeURIComponent(query.trim())}`
        );
        setResults(data);
      } catch {
        setResults([]);
      }
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, activeSiteId, selectedWorker]);

  async function selectWorker(id: string) {
    try {
      const w = await api.get<Worker>(`/workers/${id}`);
      setSelectedWorker(w);
      setResults([]);
      setQuery("");
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not load worker.", "error");
    }
  }

  function addToCart() {
    const item = items.find((i) => i.id === pickItemId);
    if (!item) return;
    const qty = Math.max(1, Number(pickQty) || 1);
    setCart((c) => {
      const existing = c.find((l) => l.item.id === item.id);
      if (existing) {
        return c.map((l) => (l.item.id === item.id ? { ...l, quantity: l.quantity + qty } : l));
      }
      return [...c, { item, quantity: qty }];
    });
    setPickItemId("");
    setPickQty("1");
  }

  function removeFromCart(itemId: string) {
    setCart((c) => c.filter((l) => l.item.id !== itemId));
  }

  async function handleIssueAll() {
    if (!selectedWorker || cart.length === 0) return;
    setIssuing(true);
    try {
      const txns = await api.post<TransactionOut[]>("/transactions/issue", {
        worker_id: selectedWorker.id,
        items: cart.map((l) => ({ inventory_item_id: l.item.id, quantity: l.quantity })),
      });
      setLastIssued(txns);
      setCart([]);
      notify(`${txns.length} item(s) issued to ${selectedWorker.full_name}.`);
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not issue items.", "error");
    } finally {
      setIssuing(false);
    }
  }

  if (!activeSiteId) return <LoadingBlock />;

  // Step 1: pick a worker
  if (!selectedWorker) {
    return (
      <div className="space-y-4">
        <Input
          autoFocus
          placeholder="Search worker by name, store number, ID, or phone"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {results.length > 0 && (
          <div className="space-y-1.5">
            {results.map((w) => (
              <button
                key={w.id}
                onClick={() => selectWorker(w.id)}
                className="flex w-full items-center justify-between rounded-sm border border-line bg-panel px-4 py-3.5 text-left active:bg-concrete-dim"
              >
                <div>
                  <p className="font-medium text-ink">{w.full_name}</p>
                  <p className="font-data text-sm text-ink-soft">#{w.store_number}</p>
                </div>
              </button>
            ))}
          </div>
        )}
        {query && results.length === 0 && (
          <p className="pt-4 text-center text-sm text-ink-soft">No matching workers.</p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-sm border border-line bg-panel px-4 py-3.5">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-ink">{selectedWorker.full_name}</p>
            <p className="font-data text-sm text-ink-soft">#{selectedWorker.store_number}</p>
          </div>
          <Button
            variant="ghost"
            className="min-h-0 px-2 py-1 text-xs"
            onClick={() => {
              setSelectedWorker(null);
              setLastIssued(null);
              setCart([]);
            }}
          >
            Change worker
          </Button>
        </div>
      </div>

      {lastIssued && lastIssued.length > 0 && (
        <div className="rounded-sm border border-moss/40 bg-moss/10 px-4 py-3 text-sm">
          <p className="font-medium text-moss">✓ Issued successfully</p>
          <ul className="mt-1 space-y-0.5 text-ink">
            {lastIssued.map((t) => (
              <li key={t.id}>
                {t.inventory_item_name} × {t.quantity}
              </li>
            ))}
          </ul>
        </div>
      )}

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-ink-soft">
          Add item
        </h2>
        <div className="flex gap-2">
          <Select value={pickItemId} onChange={(e) => setPickItemId(e.target.value)} className="flex-1">
            <option value="">Select item…</option>
            {items.map((i) => (
              <option key={i.id} value={i.id} disabled={i.available_quantity <= 0}>
                {i.name} ({i.available_quantity} available)
              </option>
            ))}
          </Select>
          <Input
            type="number"
            min={1}
            value={pickQty}
            onChange={(e) => setPickQty(e.target.value)}
            className="w-20"
          />
        </div>
        <Button variant="secondary" fullWidth className="mt-2" onClick={addToCart} disabled={!pickItemId}>
          + Add to visit
        </Button>
      </section>

      {cart.length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-ink-soft">
            Items for this visit
          </h2>
          <div className="space-y-1.5">
            {cart.map((l) => (
              <div
                key={l.item.id}
                className="flex items-center justify-between rounded-sm border border-line bg-panel px-4 py-3"
              >
                <p className="text-ink">
                  {l.item.name} <span className="font-data text-ink-soft">× {l.quantity}</span>
                </p>
                <button
                  onClick={() => removeFromCart(l.item.id)}
                  className="text-sm font-medium text-rust"
                  aria-label={`Remove ${l.item.name}`}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          <Button fullWidth className="mt-3" onClick={handleIssueAll} disabled={issuing}>
            {issuing ? "Issuing…" : `Issue ${cart.length} item${cart.length > 1 ? "s" : ""}`}
          </Button>
        </section>
      )}
    </div>
  );
}
