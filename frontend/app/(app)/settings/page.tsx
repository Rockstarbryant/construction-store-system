"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui";

export default function SettingsPage() {
  const { user, sites, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="space-y-6">
      <section className="rounded-sm border border-line bg-panel p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-steel text-lg font-semibold text-white">
            {user.full_name[0]?.toUpperCase()}
          </div>
          <div>
            <p className="font-medium text-ink">{user.full_name}</p>
            <p className="text-sm text-ink-soft">{user.email}</p>
          </div>
        </div>
        <p className="mt-3 text-sm text-ink-soft">
          Role: <span className="font-medium text-ink">{user.role}</span>
        </p>
      </section>

      <section>
        <h2 className="mb-2.5 text-sm font-semibold uppercase tracking-wide text-ink-soft">
          Sites
        </h2>
        <div className="space-y-1.5">
          {sites.map((s) => (
            <Link
              key={s.id}
              href={`/sites/${s.id}`}
              className="block rounded-sm border border-line bg-panel px-4 py-3.5"
            >
              <p className="font-medium text-ink">{s.name}</p>
              {s.location && <p className="text-sm text-ink-soft">{s.location}</p>}
            </Link>
          ))}
        </div>
        {user.role === "ADMIN" && (
          <Link href="/sites/new">
            <Button variant="secondary" fullWidth className="mt-2.5">
              + New site
            </Button>
          </Link>
        )}
      </section>

      {(user.role === "ADMIN" || user.role === "MANAGER") && (
        <section>
          <h2 className="mb-2.5 text-sm font-semibold uppercase tracking-wide text-ink-soft">
            Reports
          </h2>
          <Link
            href="/reports"
            className="block rounded-sm border border-line bg-panel px-4 py-3.5 font-medium text-ink"
          >
            Daily &amp; inventory reports
          </Link>
        </section>
      )}

      {user.role === "ADMIN" && (
        <section>
          <h2 className="mb-2.5 text-sm font-semibold uppercase tracking-wide text-ink-soft">
            Administration
          </h2>
          <Link
            href="/audit-logs"
            className="block rounded-sm border border-line bg-panel px-4 py-3.5 font-medium text-ink"
          >
            Audit log
          </Link>
        </section>
      )}

      <Button variant="danger" fullWidth onClick={logout}>
        Log out
      </Button>
    </div>
  );
}
