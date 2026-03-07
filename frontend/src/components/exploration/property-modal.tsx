"use client";

import { useCallback, useEffect } from "react";
import type { Deal } from "@/interfaces/api";
import type { PropertyData } from "./property-card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface PropertyModalProps {
  properties: PropertyData[];
  currentIndex: number;
  onClose: () => void;
  onNavigate: (index: number) => void;
  subjectDeal?: Deal | null;
}

function formatValue(value: unknown): string {
  if (value == null) return "-";
  if (typeof value === "number") {
    if (Math.abs(value) < 1) {
      return `${(value * 100).toFixed(1)}%`;
    }
    if (Math.abs(value) >= 1_000_000) {
      return `$${(value / 1_000_000).toFixed(2)}M`;
    }
    if (Math.abs(value) >= 1_000) {
      return `$${(value / 1_000).toFixed(0)}K`;
    }
    return value.toFixed(2);
  }
  return String(value);
}

const DISPLAY_KEYS = [
  "address",
  "property_type",
  "cap_rate",
  "rent_per_sqft",
  "sale_price",
  "noi",
  "square_feet",
  "year_built",
  "unit_count",
  "occupancy_rate",
  "price_per_sqft",
  "price_per_unit",
];

function formatKeyLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/Sqft/g, "SF")
    .replace(/Noi/g, "NOI");
}

export function PropertyModal({
  properties,
  currentIndex,
  onClose,
  onNavigate,
  subjectDeal,
}: PropertyModalProps) {
  const property = properties[currentIndex];
  const total = properties.length;

  const goPrev = useCallback(() => {
    if (currentIndex > 0) onNavigate(currentIndex - 1);
  }, [currentIndex, onNavigate]);

  const goNext = useCallback(() => {
    if (currentIndex < total - 1) onNavigate(currentIndex + 1);
  }, [currentIndex, total, onNavigate]);

  // Keyboard navigation
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft" || e.key === "k") goPrev();
      if (e.key === "ArrowRight" || e.key === "j") goNext();
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [goPrev, goNext]);

  if (!property) return null;

  // Collect all keys to display
  const keys = DISPLAY_KEYS.filter((k) => property[k] != null);
  // Also include any extra keys not in the predefined list
  Object.keys(property).forEach((k) => {
    if (!keys.includes(k) && property[k] != null && k !== "address") {
      keys.push(k);
    }
  });

  // Build subject deal lookup for "vs Subject" column
  const subjectValues: Record<string, unknown> = {};
  if (subjectDeal) {
    const d = subjectDeal as unknown as Record<string, unknown>;
    for (const k of keys) {
      if (d[k] != null) subjectValues[k] = d[k];
    }
  }

  const showSubject = subjectDeal && Object.keys(subjectValues).length > 0;

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="text-lg">
              {property.address}
            </DialogTitle>
            <span className="text-sm text-muted-foreground shrink-0">
              {currentIndex + 1} of {total}
            </span>
          </div>
        </DialogHeader>

        {/* Property details table */}
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted/50">
                <th className="text-left px-4 py-2 font-medium">Field</th>
                <th className="text-left px-4 py-2 font-medium">Value</th>
                {showSubject && (
                  <th className="text-left px-4 py-2 font-medium">
                    vs Subject
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {keys.map((key) => (
                <tr key={key} className="border-t">
                  <td className="px-4 py-2 text-muted-foreground">
                    {formatKeyLabel(key)}
                  </td>
                  <td className="px-4 py-2 font-medium">
                    {formatValue(property[key])}
                  </td>
                  {showSubject && (
                    <td className="px-4 py-2 text-muted-foreground">
                      {subjectValues[key] != null
                        ? formatValue(subjectValues[key])
                        : "-"}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <DialogFooter className="flex-row justify-between sm:justify-between">
          <Button
            variant="outline"
            size="sm"
            disabled={currentIndex === 0}
            onClick={goPrev}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={currentIndex === total - 1}
            onClick={goNext}
          >
            Next
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
