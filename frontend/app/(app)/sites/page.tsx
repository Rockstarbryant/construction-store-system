"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button, EmptyState } from "@/components/ui";

export default function SitesPage() {
  const { sites, user } = useAuth();

  return (
    <div className="space-y-4">
      {user?.role === "ADMIN" && (
        <Link href="/sites/new">
          <Button variant="secondary" fullWidth>
            + New site
          </Button>
        </Link>
      )}

      {sites.length === 0 ? (
        <EmptyState title="No sites yet" description="Create your first construction site." />
      ) : (
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
      )}
    </div>
  );
}
