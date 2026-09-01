"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { Worker } from "@/lib/types";
import { useToast } from "@/lib/toast-context";
import { Button, FieldError, Input, Label, Spinner } from "@/components/ui";

export default function NewWorkerPage() {
  const { activeSiteId } = useAuth();
  const router = useRouter();
  const { notify } = useToast();

  const [fullName, setFullName] = useState("");
  const [nationalId, setNationalId] = useState("");
  const [phone, setPhone] = useState("");
  const [jobRole, setJobRole] = useState("");
  const [supervisor, setSupervisor] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [registered, setRegistered] = useState<Worker | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!activeSiteId) return;
    setError(null);
    setSubmitting(true);
    try {
      const worker = await api.post<Worker>("/workers", {
        site_id: activeSiteId,
        full_name: fullName,
        national_id: nationalId,
        phone_number: phone,
        job_role: jobRole || undefined,
        supervisor: supervisor || undefined,
      });
      setRegistered(worker);
      notify(`Worker registered — Store Number ${worker.store_number}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not register worker.");
    } finally {
      setSubmitting(false);
    }
  }

  if (registered) {
    return (
      <div className="flex flex-col items-center gap-4 rounded-sm border border-moss/40 bg-moss/10 px-6 py-12 text-center">
        <p className="font-display text-lg font-semibold text-ink">Worker registered successfully</p>
        <p className="text-ink-soft">{registered.full_name}</p>
        <p className="font-data text-4xl font-bold text-ink">#{registered.store_number}</p>
        <div className="mt-2 flex w-full max-w-xs flex-col gap-2.5">
          <Button onClick={() => router.push(`/workers/${registered.id}`)} fullWidth>
            View profile
          </Button>
          <Button
            variant="secondary"
            fullWidth
            onClick={() => {
              setRegistered(null);
              setFullName("");
              setNationalId("");
              setPhone("");
              setJobRole("");
              setSupervisor("");
            }}
          >
            Register another worker
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <Label htmlFor="fullName">Full name</Label>
        <Input id="fullName" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
      </div>
      <div>
        <Label htmlFor="nationalId">National ID number</Label>
        <Input
          id="nationalId"
          required
          value={nationalId}
          onChange={(e) => setNationalId(e.target.value)}
        />
      </div>
      <div>
        <Label htmlFor="phone">Phone number</Label>
        <Input
          id="phone"
          required
          placeholder="0712345678"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />
      </div>
      <div>
        <Label htmlFor="jobRole">Job role (optional)</Label>
        <Input id="jobRole" value={jobRole} onChange={(e) => setJobRole(e.target.value)} />
      </div>
      <div>
        <Label htmlFor="supervisor">Supervisor (optional)</Label>
        <Input id="supervisor" value={supervisor} onChange={(e) => setSupervisor(e.target.value)} />
      </div>
      <FieldError>{error ?? undefined}</FieldError>
      <Button type="submit" fullWidth disabled={submitting}>
        {submitting ? <Spinner className="h-5 w-5" /> : "Register worker"}
      </Button>
    </form>
  );
}
