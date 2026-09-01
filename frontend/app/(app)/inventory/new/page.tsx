"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { InventoryItem, ItemType } from "@/lib/types";
import { useToast } from "@/lib/toast-context";
import { Button, FieldError, Input, Label, Select, Spinner } from "@/components/ui";

export default function NewInventoryItemPage() {
  const { activeSiteId } = useAuth();
  const router = useRouter();
  const { notify } = useToast();

  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [itemType, setItemType] = useState<ItemType>("CONSUMABLE");
  const [initialQuantity, setInitialQuantity] = useState("0");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!activeSiteId) return;
    setError(null);
    setSubmitting(true);
    try {
      const item = await api.post<InventoryItem>("/inventory", {
        site_id: activeSiteId,
        name,
        category: category || undefined,
        item_type: itemType,
        initial_quantity: itemType === "CONSUMABLE" ? Number(initialQuantity) || 0 : 0,
      });
      notify(`${item.name} added to inventory.`);
      router.push(`/inventory/${item.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create item.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <Label htmlFor="name">Item name</Label>
        <Input id="name" required value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div>
        <Label htmlFor="category">Category (optional)</Label>
        <Input
          id="category"
          placeholder="e.g. Hand Tools, PPE, Power Equipment"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        />
      </div>
      <div>
        <Label htmlFor="itemType">Tracking type</Label>
        <Select id="itemType" value={itemType} onChange={(e) => setItemType(e.target.value as ItemType)}>
          <option value="CONSUMABLE">Consumable — tracked by quantity</option>
          <option value="ASSET">Individually tracked asset (add units after creating)</option>
        </Select>
      </div>
      {itemType === "CONSUMABLE" && (
        <div>
          <Label htmlFor="qty">Initial quantity</Label>
          <Input
            id="qty"
            type="number"
            min={0}
            value={initialQuantity}
            onChange={(e) => setInitialQuantity(e.target.value)}
          />
        </div>
      )}
      <FieldError>{error ?? undefined}</FieldError>
      <Button type="submit" fullWidth disabled={submitting}>
        {submitting ? <Spinner className="h-5 w-5" /> : "Add item"}
      </Button>
    </form>
  );
}
