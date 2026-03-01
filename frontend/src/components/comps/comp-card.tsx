"use client";

import type { Comp } from "@/interfaces/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

interface DotLineChartProps {
  subjectValue: number | null;
  compValue: number | null;
  min: number;
  max: number;
  format: (v: number) => string;
  label: string;
}

function DotLineChart({ subjectValue, compValue, min, max, format, label }: DotLineChartProps) {
  const range = max - min || 1;

  function pct(value: number | null): number {
    if (value === null) return 0;
    return Math.max(0, Math.min(100, ((value - min) / range) * 100));
  }

  const hasSubject = subjectValue !== null;
  const hasComp = compValue !== null;

  if (!hasSubject && !hasComp) return null;

  return (
    <div className="mb-3">
      <div className="text-xs text-muted-foreground mb-1">{label}</div>
      <div className="relative h-6">
        {/* Track */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-muted -translate-y-1/2" />
        {/* Subject dot (blue) */}
        {hasSubject && (
          <div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 flex flex-col items-center"
            style={{ left: `${pct(subjectValue)}%` }}
          >
            <div className="w-3 h-3 rounded-full bg-blue-600 border-2 border-white shadow" />
          </div>
        )}
        {/* Comp dot (orange) */}
        {hasComp && (
          <div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 flex flex-col items-center"
            style={{ left: `${pct(compValue)}%` }}
          >
            <div className="w-3 h-3 rounded-full bg-orange-500 border-2 border-white shadow" />
          </div>
        )}
      </div>
      <div className="flex justify-between text-xs mt-1">
        <span className="text-blue-600 font-medium">
          {hasSubject ? `Subject: ${format(subjectValue!)}` : "Subject: N/A"}
        </span>
        <span className="text-orange-500 font-medium">
          {hasComp ? `This: ${format(compValue!)}` : "This: N/A"}
        </span>
      </div>
    </div>
  );
}

const METRIC_CONFIG: Array<{
  key: keyof Comp;
  label: string;
  format: (v: number) => string;
}> = [
  { key: "cap_rate", label: "Cap Rate", format: (v) => `${(v * 100).toFixed(1)}%` },
  { key: "price_per_unit", label: "Price/Unit", format: (v) => `$${Math.round(v).toLocaleString()}` },
  { key: "price_per_sqft", label: "Price/Sqft", format: (v) => `$${v.toFixed(0)}` },
  { key: "rent_per_unit", label: "Rent/Unit", format: (v) => `$${Math.round(v).toLocaleString()}` },
  { key: "occupancy_rate", label: "Occupancy", format: (v) => `${(v * 100).toFixed(0)}%` },
  { key: "expense_ratio", label: "Expense Ratio", format: (v) => `${(v * 100).toFixed(0)}%` },
  { key: "year_built", label: "Year Built", format: (v) => v.toString() },
  { key: "unit_count", label: "Units", format: (v) => v.toString() },
];

interface CompCardProps {
  comp: Comp;
  subjectMetrics: Partial<Record<keyof Comp, number>>;
  ranges: Partial<Record<keyof Comp, { min: number; max: number }>>;
}

export function CompCard({ comp, subjectMetrics, ranges }: CompCardProps) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="font-semibold text-sm leading-tight">{comp.address}</div>
            <div className="text-xs text-muted-foreground mt-0.5">
              {comp.city}, {comp.state}
            </div>
          </div>
          <Badge
            variant={comp.source === "rentcast" ? "default" : "secondary"}
            className="text-xs shrink-0"
          >
            {comp.source === "rentcast" ? "Rentcast" : "Tavily"}
          </Badge>
        </div>
        <div className="flex gap-3 text-xs text-muted-foreground mt-1">
          {comp.unit_count && <span>{comp.unit_count} units</span>}
          {comp.year_built && <span>Built {comp.year_built}</span>}
          {comp.square_feet && <span>{comp.square_feet.toLocaleString()} sqft</span>}
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        {METRIC_CONFIG.map(({ key, label, format }) => {
          const compVal = comp[key] as number | null;
          const subjectVal = (subjectMetrics[key] ?? null) as number | null;
          const range = ranges[key];

          if (compVal === null && subjectVal === null) return null;
          if (!range) return null;

          return (
            <DotLineChart
              key={key as string}
              label={label}
              subjectValue={subjectVal}
              compValue={compVal}
              min={range.min}
              max={range.max}
              format={format}
            />
          );
        })}
      </CardContent>
    </Card>
  );
}
