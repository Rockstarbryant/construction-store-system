"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export function TopBar({ title }: { title: string }) {
  const { user, sites, activeSiteId, setActiveSiteId } = useAuth();

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-concrete/95 backdrop-blur">
      <div className="mx-auto flex max-w-2xl items-center justify-between gap-3 px-4 py-3.5">
        <h1 className="font-display text-xl font-semibold text-ink">{title}</h1>
        <div className="flex items-center gap-2">
          {sites.length > 1 && (
            <select
              value={activeSiteId ?? ""}
              onChange={(e) => setActiveSiteId(e.target.value)}
              className="min-h-[40px] rounded-sm border border-line bg-panel px-2 text-sm text-ink"
              aria-label="Active site"
            >
              {sites.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          )}
          <Link
            href="/settings"
            className="flex h-10 w-10 items-center justify-center rounded-full bg-steel text-sm font-semibold text-white"
            aria-label="Settings"
          >
            {user?.full_name?.[0]?.toUpperCase() ?? "?"}
          </Link>
        </div>
      </div>
    </header>
  );
}
