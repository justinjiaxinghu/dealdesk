"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { CreateDealInput, QuickExtractResult } from "@/interfaces/api";
import { dealService } from "@/services/deal.service";
import { documentService } from "@/services/document.service";

const PROPERTY_TYPES = [
  { value: "multifamily", label: "Multifamily" },
  { value: "office", label: "Office" },
  { value: "retail", label: "Retail" },
  { value: "industrial", label: "Industrial" },
  { value: "mixed_use", label: "Mixed-Use" },
  { value: "other", label: "Other" },
];

export function CreateDealForm() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);

  // Form field state (populated by quick-extract)
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [propertyType, setPropertyType] = useState("");
  const [squareFeet, setSquareFeet] = useState("");

  // Create a blob URL for the PDF preview
  const pdfUrl = useMemo(() => {
    if (!file) return null;
    return URL.createObjectURL(file);
  }, [file]);

  // Clean up blob URL on unmount or file change
  useEffect(() => {
    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    };
  }, [pdfUrl]);

  // Trigger quick extraction when file is selected
  useEffect(() => {
    if (!file) return;

    let cancelled = false;
    setExtracting(true);
    setError(null);

    documentService
      .quickExtract(file)
      .then((result) => {
        if (cancelled) return;
        if (result.name) setName(result.name);
        if (result.address) setAddress(result.address);
        if (result.city) setCity(result.city);
        if (result.state) setState(result.state);
        if (result.property_type) setPropertyType(result.property_type);
        if (result.square_feet) setSquareFeet(String(result.square_feet));
      })
      .catch((err) => {
        if (cancelled) return;
        // Non-blocking: extraction failure shouldn't prevent manual entry
        console.warn("Quick extract failed:", err);
      })
      .finally(() => {
        if (!cancelled) setExtracting(false);
      });

    return () => {
      cancelled = true;
    };
  }, [file]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const input: CreateDealInput = {
      name,
      address,
      city,
      state,
      property_type: propertyType,
    };

    if (squareFeet) {
      input.square_feet = parseFloat(squareFeet);
    }

    try {
      const deal = await dealService.create(input);

      if (file) {
        await documentService.upload(deal.id, file);
      }

      router.push(`/deals/${deal.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create deal");
      setSubmitting(false);
    }
  }

  function handleFileChange(selectedFile: File | null) {
    setFile(selectedFile);
    // Reset form fields when file changes
    if (!selectedFile) {
      setName("");
      setAddress("");
      setCity("");
      setState("");
      setPropertyType("");
      setSquareFeet("");
    }
  }

  // Before file is selected: centered upload zone
  if (!file) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="rounded-lg border-2 border-dashed border-blue-300 bg-blue-50/50 p-10 flex flex-col items-center text-center space-y-4 max-w-lg w-full">
          <div className="text-5xl">📄</div>
          <h2 className="text-xl font-semibold">Upload Offering Memorandum</h2>
          <p className="text-sm text-muted-foreground max-w-sm">
            Upload a PDF and we'll extract deal data, generate benchmarks, and
            build your proforma automatically.
          </p>
          <input
            id="file"
            type="file"
            accept=".pdf"
            onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
            className="hidden"
          />
          <label
            htmlFor="file"
            className="inline-flex items-center justify-center gap-2 rounded-md bg-blue-600 px-8 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 cursor-pointer transition-colors"
          >
            Choose PDF File
          </label>
        </div>
      </div>
    );
  }

  // After file is selected: split layout
  return (
    <div className="flex gap-6 min-h-[80vh]">
      {/* Left: PDF preview */}
      <div className="flex-1 min-w-0 rounded-lg border bg-muted/30 overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/50">
          <span className="text-sm font-medium truncate">{file.name}</span>
          <button
            type="button"
            onClick={() => handleFileChange(null)}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Change file
          </button>
        </div>
        {pdfUrl && (
          <iframe
            src={pdfUrl}
            className="flex-1 w-full"
            title="PDF Preview"
          />
        )}
      </div>

      {/* Right: Deal details form */}
      <form
        onSubmit={handleSubmit}
        className="w-[400px] shrink-0 space-y-5 overflow-y-auto"
      >
        <h2 className="text-lg font-semibold">Deal Details</h2>
        {extracting ? (
          <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 border border-blue-200 px-4 py-3 rounded">
            <svg
              className="animate-spin h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Extracting deal info from PDF...
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            We extracted what we could from the OM. Review and adjust as needed.
          </p>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
            {error}
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="name">Deal Name</Label>
          <Input
            id="name"
            name="name"
            required
            disabled={extracting}
            placeholder="e.g. 100 Main St Acquisition"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="property_type">Property Type</Label>
          <select
            id="property_type"
            name="property_type"
            required
            disabled={extracting}
            value={propertyType}
            onChange={(e) => setPropertyType(e.target.value)}
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <option value="">Select property type...</option>
            {PROPERTY_TYPES.map((pt) => (
              <option key={pt.value} value={pt.value}>
                {pt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="address">Address</Label>
          <Input
            id="address"
            name="address"
            required
            disabled={extracting}
            placeholder="100 Main St"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="city">City</Label>
            <Input
              id="city"
              name="city"
              required
              disabled={extracting}
              placeholder="Dallas"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="state">State</Label>
            <Input
              id="state"
              name="state"
              required
              disabled={extracting}
              placeholder="TX"
              maxLength={2}
              value={state}
              onChange={(e) => setState(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="square_feet">Square Feet (optional)</Label>
          <Input
            id="square_feet"
            name="square_feet"
            type="number"
            disabled={extracting}
            placeholder="e.g. 50000"
            value={squareFeet}
            onChange={(e) => setSquareFeet(e.target.value)}
          />
        </div>

        <Button
          type="submit"
          disabled={submitting || extracting}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 text-base"
        >
          {submitting ? "Creating & Processing..." : "Create Deal & Process OM"}
        </Button>
      </form>
    </div>
  );
}
