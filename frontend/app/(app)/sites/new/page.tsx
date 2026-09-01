"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Company, Site } from "@/lib/types";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import { Button, FieldError, Input, Label, Select, Spinner } from "@/components/ui";

export default function NewSitePage() {
  const router = useRouter();
  const { notify } = useToast();
  const { refreshSites, setActiveSiteId } = useAuth();

  const [companies, setCompanies] = useState<Company[]>([]);
  const [companyId, setCompanyId] = useState("");
  const [newCompanyName, setNewCompanyName] = useState("");
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api
      .get<Company[]>("/companies")
      .then((data) => {
        setCompanies(data);
        if (data.length > 0) setCompanyId(data[0].id);
      })
      .catch(() => setCompanies([]));
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      let finalCompanyId = companyId;
      if (!finalCompanyId) {
        if (!newCompanyName.trim()) {
          setError("Enter a company name.");
          setSubmitting(false);
          return;
        }
        const company = await api.post<Company>("/companies", { name: newCompanyName });
        finalCompanyId = company.id;
      }
      const site = await api.post<Site>("/sites", {
        company_id: finalCompanyId,
        name,
        location: location || undefined,
      });
      notify(`${site.name} created.`);
      await refreshSites();
      setActiveSiteId(site.id);
      router.push(`/sites/${site.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create site.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <Label htmlFor="company">Company</Label>
        {companies.length > 0 ? (
          <Select id="company" value={companyId} onChange={(e) => setCompanyId(e.target.value)}>
            {companies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
            <option value="">+ New company…</option>
          </Select>
        ) : (
          <Input
            id="company"
            placeholder="Company name"
            value={newCompanyName}
            onChange={(e) => setNewCompanyName(e.target.value)}
          />
        )}
        {companies.length > 0 && !companyId && (
          <Input
            className="mt-2"
            placeholder="New company name"
            value={newCompanyName}
            onChange={(e) => setNewCompanyName(e.target.value)}
          />
        )}
      </div>
      <div>
        <Label htmlFor="name">Site name</Label>
        <Input id="name" required value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div>
        <Label htmlFor="location">Location (optional)</Label>
        <Input id="location" value={location} onChange={(e) => setLocation(e.target.value)} />
      </div>
      <FieldError>{error ?? undefined}</FieldError>
      <Button type="submit" fullWidth disabled={submitting}>
        {submitting ? <Spinner className="h-5 w-5" /> : "Create site"}
      </Button>
    </form>
  );
}
