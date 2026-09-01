"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { BottomNav } from "@/components/bottom-nav";
import { TopBar } from "@/components/top-bar";
import { LoadingBlock } from "@/components/ui";

const TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/workers": "Workers",
  "/workers/new": "Register Worker",
  "/inventory": "Inventory",
  "/inventory/new": "New Item",
  "/transactions": "Issue Items",
  "/transactions/outstanding": "Outstanding Items",
  "/reports": "Reports",
  "/audit-logs": "Audit Log",
  "/settings": "Settings",
  "/sites": "Sites",
  "/sites/new": "New Site",
};

function titleFor(pathname: string): string {
  if (TITLES[pathname]) return TITLES[pathname];
  if (pathname.startsWith("/workers/")) return "Worker Profile";
  if (pathname.startsWith("/inventory/")) return "Item Detail";
  if (pathname.startsWith("/sites/")) return "Site Detail";
  return "Site Store";
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, sites, activeSiteId } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <LoadingBlock />
      </div>
    );
  }

  const needsSite = pathname !== "/settings" && pathname !== "/sites" && pathname !== "/sites/new";
  const noSiteYet = needsSite && sites.length === 0;

  return (
    <div className="flex min-h-dvh flex-col">
      <TopBar title={titleFor(pathname)} />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 pb-24 pt-4">
        {noSiteYet ? (
          <div className="rounded-sm border border-dashed border-line px-6 py-14 text-center">
            <p className="font-display text-lg font-semibold text-ink">No site set up yet</p>
            <p className="mt-2 text-sm text-ink-soft">
              {user.role === "ADMIN"
                ? "Create a site to start registering workers and inventory."
                : "Ask an administrator to set up a site and add you to it."}
            </p>
            {user.role === "ADMIN" && (
              <a
                href="/sites/new"
                className="mt-4 inline-flex min-h-[48px] items-center justify-center rounded-sm bg-ink px-5 text-[15px] font-semibold text-concrete"
              >
                Create site
              </a>
            )}
          </div>
        ) : (
          children
        )}
      </main>
      <BottomNav />
    </div>
  );
}
