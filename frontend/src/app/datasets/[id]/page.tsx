"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Dataset } from "@/interfaces/api";
import { datasetService } from "@/services/dataset.service";

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

// Determine which columns have data across all properties
function getActiveColumns(properties: Record<string, unknown>[]) {
  const allKeys = new Set<string>();
  for (const p of properties) {
    for (const [k, v] of Object.entries(p)) {
      if (v != null && v !== "") allKeys.add(k);
    }
  }

  const columnDefs: { key: string; label: string; format: (v: unknown) => string }[] = [
    { key: "address", label: "Address", format: (v) => String(v) },
    { key: "property_type", label: "Type", format: (v) => String(v) },
    { key: "sale_price", label: "Sale Price", format: (v) => formatCurrency(Number(v)) },
    { key: "cap_rate", label: "Cap Rate", format: (v) => formatPercent(Number(v)) },
    { key: "noi", label: "NOI", format: (v) => formatCurrency(Number(v)) },
    { key: "rent_per_unit", label: "Rent/Unit", format: (v) => `$${Number(v).toLocaleString()}` },
    { key: "rent_per_sqft", label: "Rent/SF", format: (v) => `$${Number(v).toFixed(2)}` },
    { key: "occupancy_rate", label: "Occupancy", format: (v) => formatPercent(Number(v)) },
    { key: "vacancy_rate", label: "Vacancy", format: (v) => formatPercent(Number(v)) },
    { key: "price_per_unit", label: "Price/Unit", format: (v) => formatCurrency(Number(v)) },
    { key: "price_per_sqft", label: "Price/SF", format: (v) => `$${Number(v).toFixed(2)}` },
    { key: "expense_ratio", label: "Exp Ratio", format: (v) => formatPercent(Number(v)) },
    { key: "opex_per_unit", label: "OpEx/Unit", format: (v) => formatCurrency(Number(v)) },
    { key: "unit_count", label: "Units", format: (v) => String(v) },
    { key: "square_feet", label: "Sq Ft", format: (v) => Number(v).toLocaleString() },
    { key: "year_built", label: "Year Built", format: (v) => String(v) },
  ];

  return columnDefs.filter((col) => allKeys.has(col.key));
}

function PropertyDetailModal({
  property,
  open,
  onOpenChange,
}: {
  property: Record<string, unknown> | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  if (!property) return null;

  const entries = Object.entries(property).filter(
    ([, v]) => v != null && v !== ""
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="leading-tight">
            {String(property.address || "Property Details")}
          </DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-x-6 gap-y-2">
          {entries.map(([key, value]) => (
            <div key={key} className="flex justify-between text-sm">
              <span className="text-muted-foreground capitalize">
                {key.replace(/_/g, " ")}
              </span>
              <span className="font-medium">{String(value)}</span>
            </div>
          ))}
        </div>
        {property.source_url != null && (
          <a
            href={String(property.source_url)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:underline mt-2"
          >
            View Source
          </a>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function DatasetDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedProperty, setSelectedProperty] = useState<Record<string, unknown> | null>(null);
  const [editingName, setEditingName] = useState(false);
  const [nameValue, setNameValue] = useState("");

  useEffect(() => {
    datasetService
      .get(id)
      .then((ds) => {
        setDataset(ds);
        setNameValue(ds.name);
      })
      .catch((err) => console.error("Failed to load dataset", err))
      .finally(() => setLoading(false));
  }, [id]);

  const handleSaveName = useCallback(async () => {
    if (!dataset || !nameValue.trim()) return;
    try {
      const updated = await datasetService.update(dataset.id, {
        name: nameValue.trim(),
      });
      setDataset(updated);
      setEditingName(false);
    } catch (err) {
      console.error("Failed to rename dataset", err);
    }
  }, [dataset, nameValue]);

  const handleRemoveProperty = useCallback(
    async (index: number) => {
      if (!dataset) return;
      const updated = dataset.properties.filter((_, i) => i !== index);
      try {
        const result = await datasetService.update(dataset.id, {
          properties: updated,
        });
        setDataset(result);
      } catch (err) {
        console.error("Failed to remove property", err);
      }
    },
    [dataset]
  );

  const handleDelete = useCallback(async () => {
    if (!dataset) return;
    try {
      await datasetService.delete(dataset.id);
      router.push("/datasets");
    } catch (err) {
      console.error("Failed to delete dataset", err);
    }
  }, [dataset, router]);

  if (loading) {
    return (
      <div className="text-muted-foreground py-12">Loading dataset...</div>
    );
  }

  if (!dataset) {
    return <div className="text-red-600 py-12">Dataset not found.</div>;
  }

  const columns = getActiveColumns(dataset.properties);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/datasets"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </Link>
          {editingName ? (
            <div className="flex items-center gap-2">
              <input
                className="text-2xl font-bold border-b border-foreground bg-transparent outline-none"
                value={nameValue}
                onChange={(e) => setNameValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSaveName();
                  if (e.key === "Escape") {
                    setNameValue(dataset.name);
                    setEditingName(false);
                  }
                }}
                autoFocus
              />
              <Button size="sm" onClick={handleSaveName}>
                Save
              </Button>
            </div>
          ) : (
            <h1
              className="text-2xl font-bold cursor-pointer hover:text-muted-foreground transition-colors"
              onClick={() => setEditingName(true)}
              title="Click to rename"
            >
              {dataset.name}
            </h1>
          )}
          <Badge variant="secondary">
            {dataset.properties.length}{" "}
            {dataset.properties.length === 1 ? "property" : "properties"}
          </Badge>
          {dataset.deal_id && (
            <Badge variant="outline">Deal-linked</Badge>
          )}
        </div>
        <Button variant="destructive" size="sm" onClick={handleDelete}>
          Delete Dataset
        </Button>
      </div>

      {/* Properties table */}
      {dataset.properties.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p>No properties in this dataset yet.</p>
          <p className="text-sm mt-1">
            Add properties from search results in{" "}
            <Link href="/explore" className="text-blue-600 hover:underline">
              Explore
            </Link>
            .
          </p>
        </div>
      ) : (
        <div className="border rounded-lg overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((col) => (
                  <TableHead key={col.key}>{col.label}</TableHead>
                ))}
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {dataset.properties.map((prop, index) => (
                <TableRow
                  key={index}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => setSelectedProperty(prop)}
                >
                  {columns.map((col) => (
                    <TableCell key={col.key}>
                      {prop[col.key] != null
                        ? col.format(prop[col.key])
                        : "-"}
                    </TableCell>
                  ))}
                  <TableCell>
                    <button
                      className="p-1 rounded text-muted-foreground hover:text-red-600 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveProperty(index);
                      }}
                      title="Remove from dataset"
                    >
                      <svg
                        className="w-3.5 h-3.5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Property detail modal */}
      <PropertyDetailModal
        property={selectedProperty}
        open={selectedProperty !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedProperty(null);
        }}
      />
    </div>
  );
}
