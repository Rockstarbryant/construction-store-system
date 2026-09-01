"use client";

import { ButtonHTMLAttributes, InputHTMLAttributes, SelectHTMLAttributes, forwardRef } from "react";
import clsx from "clsx";

export const Button = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "primary" | "secondary" | "ghost" | "danger";
    fullWidth?: boolean;
  }
>(({ className, variant = "primary", fullWidth, ...props }, ref) => {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-sm px-5 py-3 text-[15px] font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-h-[48px]";
  const variants: Record<string, string> = {
    primary: "bg-ink text-concrete hover:bg-steel-dark active:bg-steel-dark",
    secondary: "bg-transparent text-ink border border-ink/70 hover:bg-ink/5",
    ghost: "bg-transparent text-steel hover:bg-steel/10",
    danger: "bg-rust text-white hover:bg-rust/90",
  };
  return (
    <button
      ref={ref}
      className={clsx(base, variants[variant], fullWidth && "w-full", className)}
      {...props}
    />
  );
});
Button.displayName = "Button";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={clsx(
        "min-h-[48px] w-full rounded-sm border border-line bg-panel px-3.5 py-2.5 text-[16px] text-ink placeholder:text-ink-soft/60 focus:border-steel",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={clsx(
        "min-h-[48px] w-full rounded-sm border border-line bg-panel px-3.5 py-2.5 text-[16px] text-ink focus:border-steel",
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
);
Select.displayName = "Select";

export function Label({ children, htmlFor }: { children: React.ReactNode; htmlFor?: string }) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium text-ink-soft">
      {children}
    </label>
  );
}

export function FieldError({ children }: { children?: string }) {
  if (!children) return null;
  return <p className="mt-1 text-sm text-rust">{children}</p>;
}

export function Spinner({ className }: { className?: string }) {
  return (
    <svg
      className={clsx("animate-spin", className)}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path
        className="opacity-90"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z"
      />
    </svg>
  );
}

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-ink-soft">
      <Spinner className="h-5 w-5" />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-sm border border-dashed border-line px-6 py-14 text-center">
      <p className="font-display text-lg font-semibold text-ink">{title}</p>
      {description && <p className="max-w-xs text-sm text-ink-soft">{description}</p>}
      {action}
    </div>
  );
}

export function ErrorBlock({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-sm border border-rust/30 bg-rust/5 px-6 py-10 text-center">
      <p className="font-medium text-rust">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

const STATUS_STRIPE: Record<string, string> = {
  ISSUED: "border-l-amber",
  RETURNED: "border-l-moss",
  ACTIVE: "border-l-moss",
  INACTIVE: "border-l-ink-soft",
  DAMAGED: "border-l-rust",
  NEEDS_REPAIR: "border-l-rust",
  LOST: "border-l-rust",
  GOOD: "border-l-moss",
  FAIR: "border-l-amber",
};

export function StripedRow({
  status,
  children,
  className,
}: {
  status?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "border-l-4 border-y border-r border-line bg-panel px-4 py-3.5",
        status ? STATUS_STRIPE[status] ?? "border-l-line" : "border-l-line",
        className
      )}
    >
      {children}
    </div>
  );
}

export function StatusText({ status }: { status: string }) {
  const colors: Record<string, string> = {
    ISSUED: "text-amber-dark",
    RETURNED: "text-moss",
    ACTIVE: "text-moss",
    INACTIVE: "text-ink-soft",
    DAMAGED: "text-rust",
    NEEDS_REPAIR: "text-rust",
    LOST: "text-rust",
    GOOD: "text-moss",
    FAIR: "text-amber-dark",
  };
  return (
    <span className={clsx("text-sm font-medium", colors[status] ?? "text-ink-soft")}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
