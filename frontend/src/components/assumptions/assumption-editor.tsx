"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Assumption } from "@/interfaces/api";
import {
  assumptionService,
  type BulkAssumptionInput,
} from "@/services/assumption.service";

function sourceTypeBadge(sourceType: string) {
  switch (sourceType.toLowerCase()) {
    case "extracted":
      return (
        <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">
          Extracted
        </Badge>
      );
    case "benchmark":
      return (
        <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100">
          Benchmark
        </Badge>
      );
    case "manual":
      return (
        <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-100">
          Manual
        </Badge>
      );
    default:
      return <Badge variant="outline">{sourceType}</Badge>;
  }
}

interface AssumptionEditorProps {
  setId: string;
  assumptions: Assumption[];
  onSaved: () => void;
}

interface EditableAssumption {
  key: string;
  value_number: string;
  unit: string;
  range_min: string;
  range_max: string;
  source_type: string;
  source_ref: string;
  notes: string;
}

function toEditable(a: Assumption): EditableAssumption {
  return {
    key: a.key,
    value_number: a.value_number?.toString() ?? "",
    unit: a.unit ?? "",
    range_min: a.range_min?.toString() ?? "",
    range_max: a.range_max?.toString() ?? "",
    source_type: a.source_type,
    source_ref: a.source_ref ?? "",
    notes: a.notes ?? "",
  };
}

export function AssumptionEditor({
  setId,
  assumptions,
  onSaved,
}: AssumptionEditorProps) {
  const [rows, setRows] = useState<EditableAssumption[]>(
    assumptions.map(toEditable),
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateRow(index: number, field: keyof EditableAssumption, value: string) {
    setRows((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: value };
      return copy;
    });
  }

  async function handleSave() {
    setSaving(true);
    setError(null);

    const payload: BulkAssumptionInput[] = rows.map((r) => ({
      key: r.key,
      value_number: r.value_number ? parseFloat(r.value_number) : null,
      unit: r.unit || null,
      range_min: r.range_min ? parseFloat(r.range_min) : null,
      range_max: r.range_max ? parseFloat(r.range_max) : null,
      source_type: r.source_type || "manual",
      source_ref: r.source_ref || null,
      notes: r.notes || null,
    }));

    try {
      await assumptionService.bulkUpdate(setId, payload);
      onSaved();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save assumptions",
      );
    } finally {
      setSaving(false);
    }
  }

  if (rows.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No assumptions yet. Generate AI benchmarks or add assumptions manually.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
          {error}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2 font-medium">Key</th>
              <th className="text-left p-2 font-medium">Value</th>
              <th className="text-left p-2 font-medium">Unit</th>
              <th className="text-left p-2 font-medium">Min</th>
              <th className="text-left p-2 font-medium">Max</th>
              <th className="text-left p-2 font-medium">Source</th>
              <th className="text-left p-2 font-medium">Notes</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={row.key} className="border-b">
                <td className="p-2 font-medium whitespace-nowrap">
                  {row.key}
                </td>
                <td className="p-2">
                  <Input
                    type="number"
                    value={row.value_number}
                    onChange={(e) =>
                      updateRow(i, "value_number", e.target.value)
                    }
                    className="w-28 h-8"
                  />
                </td>
                <td className="p-2">
                  <Input
                    value={row.unit}
                    onChange={(e) => updateRow(i, "unit", e.target.value)}
                    className="w-20 h-8"
                  />
                </td>
                <td className="p-2">
                  <Input
                    type="number"
                    value={row.range_min}
                    onChange={(e) =>
                      updateRow(i, "range_min", e.target.value)
                    }
                    className="w-24 h-8"
                  />
                </td>
                <td className="p-2">
                  <Input
                    type="number"
                    value={row.range_max}
                    onChange={(e) =>
                      updateRow(i, "range_max", e.target.value)
                    }
                    className="w-24 h-8"
                  />
                </td>
                <td className="p-2">{sourceTypeBadge(row.source_type)}</td>
                <td className="p-2">
                  <Input
                    value={row.notes}
                    onChange={(e) => updateRow(i, "notes", e.target.value)}
                    className="w-40 h-8"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Button onClick={handleSave} disabled={saving}>
        {saving ? "Saving..." : "Save Assumptions"}
      </Button>
    </div>
  );
}
