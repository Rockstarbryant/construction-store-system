"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const TABS = [
  { href: "/dashboard", label: "Home", icon: HomeIcon },
  { href: "/workers", label: "Workers", icon: PeopleIcon },
  { href: "/transactions", label: "Issue", icon: IssueIcon, emphasize: true },
  { href: "/transactions/outstanding", label: "Outstanding", icon: OutstandingIcon },
  { href: "/inventory", label: "Inventory", icon: BoxIcon },
];

export function BottomNav() {
  const pathname = usePathname();
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-panel pb-[env(safe-area-inset-bottom)]">
      <ul className="mx-auto flex max-w-2xl items-stretch justify-between">
        {TABS.map((tab) => {
          const active = pathname === tab.href || (tab.href !== "/dashboard" && pathname.startsWith(tab.href));
          const Icon = tab.icon;
          return (
            <li key={tab.href} className="flex-1">
              <Link
                href={tab.href}
                className={clsx(
                  "flex min-h-[60px] flex-col items-center justify-center gap-1 text-[11px] font-medium",
                  active ? "text-ink" : "text-ink-soft"
                )}
              >
                <Icon
                  className={clsx("h-6 w-6", tab.emphasize && !active && "text-amber-dark", active && "text-ink")}
                />
                {tab.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

function HomeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 11.5 12 4l8 7.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M6 10v9a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function PeopleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="9" cy="8" r="3" />
      <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" strokeLinecap="round" />
      <circle cx="17" cy="9" r="2.3" />
      <path d="M15 14.3c2.6.4 4.5 2.6 4.5 5.7" strokeLinecap="round" />
    </svg>
  );
}
function IssueIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="4" y="7" width="16" height="13" rx="1.2" />
      <path d="M8 7V5.5A2.5 2.5 0 0 1 10.5 3h3A2.5 2.5 0 0 1 16 5.5V7" strokeLinecap="round" />
      <path d="M12 11v5M9.5 13.5h5" strokeLinecap="round" />
    </svg>
  );
}
function OutstandingIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function BoxIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M3.5 8 12 4l8.5 4-8.5 4-8.5-4Z" strokeLinejoin="round" />
      <path d="M3.5 8v8L12 20l8.5-4V8" strokeLinejoin="round" />
      <path d="M12 12v8" />
    </svg>
  );
}
