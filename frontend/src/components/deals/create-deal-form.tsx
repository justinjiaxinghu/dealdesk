"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { CreateDealInput } from "@/interfaces/api";
import { dealService } from "@/services/deal.service";
import { documentService } from "@/services/document.service";

const PROPERTY_TYPES = [
  "Multifamily",
  "Office",
  "Retail",
  "Industrial",
  "Mixed-Use",
  "Hospitality",
  "Land",
  "Other",
];

export function CreateDealForm() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const form = e.currentTarget;
    const formData = new FormData(form);

    const input: CreateDealInput = {
      name: formData.get("name") as string,
      address: formData.get("address") as string,
      city: formData.get("city") as string,
      state: formData.get("state") as string,
      property_type: formData.get("property_type") as string,
    };

    const sqft = formData.get("square_feet") as string;
    if (sqft) {
      input.square_feet = parseFloat(sqft);
    }

    try {
      const deal = await dealService.create(input);

      // Upload file if provided
      if (file) {
        await documentService.upload(deal.id, file);
      }

      router.push(`/deals/${deal.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create deal");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="name">Deal Name</Label>
        <Input id="name" name="name" required placeholder="e.g. 100 Main St Acquisition" />
      </div>

      <div className="space-y-2">
        <Label htmlFor="address">Address</Label>
        <Input id="address" name="address" required placeholder="100 Main St" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="city">City</Label>
          <Input id="city" name="city" required placeholder="Dallas" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="state">State</Label>
          <Input id="state" name="state" required placeholder="TX" maxLength={2} />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="property_type">Property Type</Label>
        <select
          id="property_type"
          name="property_type"
          required
          className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        >
          <option value="">Select property type...</option>
          {PROPERTY_TYPES.map((pt) => (
            <option key={pt} value={pt}>
              {pt}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="square_feet">Square Feet</Label>
        <Input
          id="square_feet"
          name="square_feet"
          type="number"
          placeholder="e.g. 50000"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="file">Offering Memorandum (PDF)</Label>
        <Input
          id="file"
          type="file"
          accept=".pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <p className="text-sm text-muted-foreground">
          Upload a PDF offering memorandum to extract deal data automatically.
        </p>
      </div>

      <Button type="submit" disabled={submitting}>
        {submitting ? "Creating..." : "Create Deal"}
      </Button>
    </form>
  );
}
