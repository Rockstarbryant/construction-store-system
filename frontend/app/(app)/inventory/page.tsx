"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { InventoryItem } from "@/lib/types";
import { Button, EmptyState, ErrorBlock, LoadingBlock } from "@/components/ui";

export default function InventoryPage() {
  const { activeSiteId, user } = useAuth();
  const [items, setItems] = useState<InventoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    if (!activeSiteId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<InventoryItem[]>(`/inventory?site_id=${activeSiteId}`);
      setItems(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load inventory.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSiteId]);

  const grouped = items?.reduce<Record<string, InventoryItem[]>>((acc, item) => {
    const key = item.category ?? "Uncategorized";
    (acc[key] ??= []).push(item);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      {user?.role === "ADMIN" && (
        <Link href="/inventory/new">
          <Button variant="secondary" fullWidth>
            + Add inventory item
          </Button>
        </Link>
      )}

      {loading && <LoadingBlock />}
      {error && !loading && <ErrorBlock message={error} onRetry={load} />}

      {!loading && items && items.length === 0 && (
        <EmptyState
          title="No inventory yet"
          description="Add tools and equipment to start issuing them to workers."
        />
      )}

      {!loading && grouped && (
        <div className="space-y-5">
          {Object.entries(grouped).map(([category, catItems]) => (
            <section key={category}>
              <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-ink-soft">
                {category}
              </h2>
              <div className="space-y-1.5">
                {catItems.map((item) => (
                  <Link key={item.id} href={`/inventory/${item.id}`}>
                    <div className="flex items-center justify-between gap-3 rounded-sm border border-line bg-panel px-4 py-3.5">
                      <div>
                        <p className="font-medium text-ink">{item.name}</p>
                        <p className="text-xs text-ink-soft">
                          {item.item_type === "CONSUMABLE" ? "Consumable" : "Tracked asset"}
                        </p>
                      </div>
                      <div className="text-right font-data text-sm">
                        <p className="font-semibold text-ink">
                          {item.available_quantity}/{item.total_quantity}
                        </p>
                        <p className="text-xs text-ink-soft">available</p>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
