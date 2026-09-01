"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { WorkerSearchResult } from "@/lib/types";
import { Button, EmptyState, ErrorBlock, Input, LoadingBlock, StripedRow } from "@/components/ui";

export default function WorkersPage() {
  const { activeSiteId } = useAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<WorkerSearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!activeSiteId) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (query.trim().length === 0) {
      setResults(null);
      setError(null);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.get<WorkerSearchResult[]>(
          `/workers/search?site_id=${activeSiteId}&q=${encodeURIComponent(query.trim())}`
        );
        setResults(data);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Search failed.");
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, activeSiteId]);

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input
          autoFocus
          placeholder="Search name, store number, ID, or phone"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <Link href="/workers/new">
        <Button variant="secondary" fullWidth>
          + Register new worker
        </Button>
      </Link>

      {loading && <LoadingBlock label="Searching…" />}
      {error && !loading && <ErrorBlock message={error} />}

      {!loading && !error && results && results.length === 0 && (
        <EmptyState title="No workers found" description={`Nothing matches "${query}".`} />
      )}

      {!loading && results && results.length > 0 && (
        <div className="space-y-1.5">
          {results.map((w) => (
            <Link key={w.id} href={`/workers/${w.id}`}>
              <StripedRow status={w.status}>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-ink">{w.full_name}</p>
                    <p className="font-data text-sm text-ink-soft">
                      #{w.store_number} · {w.phone_number}
                    </p>
                  </div>
                  {w.status === "INACTIVE" && (
                    <span className="shrink-0 text-xs font-medium text-ink-soft">Inactive</span>
                  )}
                </div>
              </StripedRow>
            </Link>
          ))}
        </div>
      )}

      {!query && !results && (
        <p className="pt-6 text-center text-sm text-ink-soft">
          Start typing to search for a worker.
        </p>
      )}
    </div>
  );
}
