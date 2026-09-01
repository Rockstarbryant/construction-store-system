"use client";

import { FormEvent, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import { Button, FieldError, Input, Label, Spinner } from "@/components/ui";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to log in. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center bg-concrete px-5">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-sm bg-ink text-amber">
            <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M3.5 8 12 4l8.5 4-8.5 4-8.5-4Z" strokeLinejoin="round" />
              <path d="M3.5 8v8L12 20l8.5-4V8" strokeLinejoin="round" />
              <path d="M12 12v8" />
            </svg>
          </div>
          <h1 className="font-display text-2xl font-bold text-ink">Site Store</h1>
          <p className="mt-1 text-sm text-ink-soft">Tool Accountability System</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <FieldError>{error ?? undefined}</FieldError>
          <Button type="submit" fullWidth disabled={submitting}>
            {submitting ? <Spinner className="h-5 w-5" /> : "Log in"}
          </Button>
        </form>

        <p className="mt-6 text-center text-xs text-ink-soft">
          Demo: storekeeper@demo-construction.example.com / StorePass123!
        </p>
      </div>
    </div>
  );
}
