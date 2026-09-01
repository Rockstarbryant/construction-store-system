"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { Department, Site } from "@/lib/types";
import { useToast } from "@/lib/toast-context";
import { Button, ErrorBlock, Input, LoadingBlock } from "@/components/ui";

export default function SiteDetailPage() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const { notify } = useToast();

  const [site, setSite] = useState<Site | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newDept, setNewDept] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, depts] = await Promise.all([
        api.get<Site>(`/sites/${params.id}`),
        api.get<Department[]>(`/departments?site_id=${params.id}`),
      ]);
      setSite(s);
      setDepartments(depts);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load site.");
    } finally {
      setLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    load();
  }, [load]);

  async function addDepartment(e: FormEvent) {
    e.preventDefault();
    if (!newDept.trim() || !site) return;
    try {
      await api.post("/departments", { site_id: site.id, name: newDept.trim() });
      setNewDept("");
      await load();
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not add department.", "error");
    }
  }

  async function toggleActive() {
    if (!site) return;
    try {
      const updated = await api.patch<Site>(`/sites/${site.id}`, { is_active: !site.is_active });
      setSite(updated);
      notify(`Site marked ${updated.is_active ? "active" : "inactive"}.`);
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not update site.", "error");
    }
  }

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBlock message={error} onRetry={load} />;
  if (!site) return null;

  return (
    <div className="space-y-6">
      <section className="rounded-sm border border-line bg-panel p-4">
        <p className="font-display text-xl font-semibold text-ink">{site.name}</p>
        {site.location && <p className="text-sm text-ink-soft">{site.location}</p>}
        <p className="mt-2 text-sm">
          Status:{" "}
          <span className={site.is_active ? "text-moss" : "text-ink-soft"}>
            {site.is_active ? "Active" : "Inactive"}
          </span>
        </p>
        {user?.role === "ADMIN" && (
          <Button variant="secondary" className="mt-3" onClick={toggleActive}>
            Mark {site.is_active ? "inactive" : "active"}
          </Button>
        )}
      </section>

      <section>
        <h2 className="mb-2.5 text-sm font-semibold uppercase tracking-wide text-ink-soft">
          Departments
        </h2>
        {departments.length === 0 ? (
          <p className="pb-3 text-sm text-ink-soft">No departments yet.</p>
        ) : (
          <div className="mb-3 space-y-1.5">
            {departments.map((d) => (
              <div key={d.id} className="rounded-sm border border-line bg-panel px-4 py-2.5 text-ink">
                {d.name}
              </div>
            ))}
          </div>
        )}
        {user?.role === "ADMIN" && (
          <form onSubmit={addDepartment} className="flex gap-2">
            <Input
              placeholder="New department name"
              value={newDept}
              onChange={(e) => setNewDept(e.target.value)}
            />
            <Button type="submit" disabled={!newDept.trim()}>
              Add
            </Button>
          </form>
        )}
      </section>
    </div>
  );
}
