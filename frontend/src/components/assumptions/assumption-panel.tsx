"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Assumption } from "@/interfaces/api";

const GROUPS = [
  { key: "model_structure", label: "Model Structure" },
  { key: "transaction", label: "Transaction" },
  { key: "operating", label: "Operating" },
  { key: "financing", label: "Financing" },
  { key: "return_targets", label: "Return Targets" },
] as const;

const FORECAST_METHODS = [
  { value: "historical", label: "In-line with historicals" },
  { value: "step_change", label: "Step change" },
  { value: "gradual_ramp", label: "Gradual ramp to target" },
];

interface AssumptionPanelProps {
  assumptions: Assumption[];
  onUpdate?: (key: string, value: number | null) => void;
}

export function AssumptionPanel({ assumptions, onUpdate }: AssumptionPanelProps) {
  const [expanded, setExpanded] = useState<Set<string>>(
    new Set(["model_structure", "transaction", "operating", "financing", "return_targets"])
  );

  function toggle(key: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  if (assumptions.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No assumptions yet. AI benchmarks will be generated automatically after
        document processing completes.
      </p>
    );
  }

  const ungrouped = assumptions.filter((a) => !a.group);
  const grouped = GROUPS.map((g) => ({
    ...g,
    items: assumptions.filter((a) => a.group === g.key),
  }));

  return (
    <div className="space-y-3">
      {grouped.map((group) => {
        if (group.items.length === 0) return null;
        const isOpen = expanded.has(group.key);
        return (
          <div key={group.key} className="border rounded-lg overflow-hidden">
            <button
              type="button"
              className="w-full flex items-center justify-between px-4 py-2 bg-muted/40 hover:bg-muted/70 text-sm font-medium"
              onClick={() => toggle(group.key)}
            >
              <span>{group.label}</span>
              <span className="text-muted-foreground">{isOpen ? "▲" : "▼"}</span>
            </button>
            {isOpen && (
              <div className="divide-y">
                {group.items.map((a) => (
                  <AssumptionRow key={a.id} assumption={a} onUpdate={onUpdate} />
                ))}
              </div>
            )}
          </div>
        );
      })}

      {ungrouped.length > 0 && (
        <div className="border rounded-lg overflow-hidden">
          <button
            type="button"
            className="w-full flex items-center justify-between px-4 py-2 bg-muted/40 hover:bg-muted/70 text-sm font-medium"
            onClick={() => toggle("_other")}
          >
            <span>Other</span>
            <span className="text-muted-foreground">{expanded.has("_other") ? "▲" : "▼"}</span>
          </button>
          {expanded.has("_other") && (
            <div className="divide-y">
              {ungrouped.map((a) => (
                <AssumptionRow key={a.id} assumption={a} onUpdate={onUpdate} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AssumptionRow({
  assumption: a,
  onUpdate,
}: {
  assumption: Assumption;
  onUpdate?: (key: string, value: number | null) => void;
}) {
  const isOperating = a.group === "operating";

  return (
    <div className="px-4 py-2 flex items-start gap-3 text-sm">
      <div className="flex-1 min-w-0">
        <div className="font-medium text-xs text-muted-foreground uppercase tracking-wide mb-1">
          {a.key}
        </div>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            className="h-7 w-32 text-sm"
            defaultValue={a.value_number ?? ""}
            onBlur={(e) => onUpdate?.(a.key, e.target.value ? Number(e.target.value) : null)}
          />
          {a.unit && <span className="text-muted-foreground text-xs">{a.unit}</span>}
        </div>
      </div>
      {isOperating && (
        <div className="flex-1 min-w-0">
          <div className="text-xs text-muted-foreground mb-1">Forecast</div>
          <Select defaultValue={a.forecast_method ?? "historical"}>
            <SelectTrigger className="h-7 text-xs w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {FORECAST_METHODS.map((m) => (
                <SelectItem key={m.value} value={m.value} className="text-xs">
                  {m.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
      <div className="flex items-center pt-5">
        <SourceBadge sourceType={a.source_type} />
      </div>
    </div>
  );
}

function SourceBadge({ sourceType }: { sourceType: string }) {
  switch (sourceType.toLowerCase()) {
    case "extracted":
      return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">Extracted</Badge>;
    case "benchmark":
      return <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100">Benchmark</Badge>;
    default:
      return <Badge variant="outline">{sourceType}</Badge>;
  }
}
