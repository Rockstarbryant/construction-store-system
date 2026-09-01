"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { AuditLogEntry } from "@/lib/types";
import { EmptyState, ErrorBlock, LoadingBlock, StripedRow } from "@/components/ui";
import { formatDateTime } from "@/lib/format";

export default function AuditLogPage() {
  const { user } = useAuth();
  const [logs, setLogs] = useState<AuditLogEntry[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<AuditLogEntry[]>("/audit-logs?limit=200");
      setLogs(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load audit log.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (user?.role !== "ADMIN") {
    return (
      <EmptyState title="Admins only" description="The audit log is only visible to administrators." />
    );
  }

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBlock message={error} onRetry={load} />;
  if (!logs || logs.length === 0) return <EmptyState title="No audit entries yet" />;

  return (
    <div className="space-y-1.5">
      {logs.map((log) => (
        <StripedRow key={log.id}>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-ink">{log.action.replace(/_/g, " ")}</p>
              <p className="text-xs text-ink-soft">
                {log.entity_type}
                {log.entity_id && ` · ${log.entity_id.slice(0, 8)}`}
              </p>
            </div>
            <span className="font-data shrink-0 text-xs text-ink-soft">
              {formatDateTime(log.created_at)}
            </span>
          </div>
        </StripedRow>
      ))}
    </div>
  );
}
