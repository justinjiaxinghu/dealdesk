"use client";

import { useState } from "react";
import type { Comp, ExtractedField } from "@/interfaces/api";
import { CompCard } from "./comp-card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type MetricDef = {
  key: keyof Comp;
  label: string;
  format: (v: number) => string;
  higherIsBetter: boolean | null;
  // Direct field key match
  extractedFieldKey?: string;
  // Derived from multiple fields: return value or null
  derive?: (fields: ExtractedField[]) => number | null;
};

const GAP_METRICS: MetricDef[] = [
  {
    key: "cap_rate",
    label: "Cap Rate",
    format: (v) => `${(v * 100).toFixed(2)}%`,
    higherIsBetter: true,
    derive: (fields) => {
      const noi = fields.find((f) => f.field_key === "current_noi")?.value_number ?? null;
      const price = fields.find((f) => f.field_key === "offering_price")?.value_number ?? null;
      return noi !== null && price !== null && price > 0 ? noi / price : null;
    },
  },
  {
    key: "price_per_unit",
    label: "Price / Unit",
    format: (v) => `$${Math.round(v).toLocaleString()}`,
    higherIsBetter: false,
    derive: (fields) => {
      const price = fields.find((f) => f.field_key === "offering_price")?.value_number ?? null;
      const units = fields.find((f) => f.field_key === "number_of_units")?.value_number ?? null;
      return price !== null && units !== null && units > 0 ? price / units : null;
    },
  },
  {
    key: "price_per_sqft",
    label: "Price / Sqft",
    format: (v) => `$${v.toFixed(0)}`,
    higherIsBetter: false,
    derive: (fields) => {
      const price = fields.find((f) => f.field_key === "offering_price")?.value_number ?? null;
      const sqft = fields.find((f) => f.field_key === "total_square_feet" || f.field_key === "total_size")?.value_number ?? null;
      return price !== null && sqft !== null && sqft > 0 ? price / sqft : null;
    },
  },
  {
    key: "rent_per_unit",
    label: "Rent / Unit",
    format: (v) => `$${Math.round(v).toLocaleString()}`,
    higherIsBetter: true,
    extractedFieldKey: "rent_per_unit",
  },
  {
    key: "occupancy_rate",
    label: "Occupancy",
    format: (v) => `${(v * 100).toFixed(0)}%`,
    higherIsBetter: true,
    derive: (fields) => {
      const vacancy = fields.find((f) => f.field_key === "vacancy_rate")?.value_number ?? null;
      if (vacancy === null) return null;
      // vacancy_rate stored as percentage (e.g. 3 = 3%), convert to occupancy decimal
      const vacancyDecimal = vacancy > 1 ? vacancy / 100 : vacancy;
      return 1 - vacancyDecimal;
    },
  },
  {
    key: "expense_ratio",
    label: "Expense Ratio",
    format: (v) => `${(v * 100).toFixed(0)}%`,
    higherIsBetter: false,
    extractedFieldKey: "expense_ratio",
  },
  {
    key: "year_built",
    label: "Year Built",
    format: (v) => v.toString(),
    higherIsBetter: null,
    extractedFieldKey: "year_built",
  },
  {
    key: "unit_count",
    label: "Units",
    format: (v) => v.toString(),
    higherIsBetter: null,
    extractedFieldKey: "number_of_units",
  },
];

function avg(values: number[]): number | null {
  const valid = values.filter((v) => !isNaN(v));
  if (valid.length === 0) return null;
  return valid.reduce((a, b) => a + b, 0) / valid.length;
}

function getSubjectValue(metric: MetricDef, fields: ExtractedField[]): number | null {
  if (metric.derive) return metric.derive(fields);
  if (!metric.extractedFieldKey) return null;
  const field = fields.find((f) => f.field_key === metric.extractedFieldKey);
  return field?.value_number ?? null;
}

function computeRanges(comps: Comp[]): Partial<Record<keyof Comp, { min: number; max: number }>> {
  const ranges: Partial<Record<keyof Comp, { min: number; max: number }>> = {};
  for (const metric of GAP_METRICS) {
    const values = comps
      .map((c) => c[metric.key] as number | null)
      .filter((v): v is number => v !== null);
    if (values.length === 0) continue;
    ranges[metric.key] = { min: Math.min(...values), max: Math.max(...values) };
  }
  return ranges;
}

function gapLabel(
  subject: number | null,
  compAvg: number | null,
  metric: (typeof GAP_METRICS)[0],
): { text: string; color: string; status: string } {
  if (subject === null || compAvg === null || compAvg === 0) return { text: "—", color: "text-muted-foreground", status: "—" };
  const diff = subject - compAvg;
  const pct = Math.round((diff / compAvg) * 100);
  const sign = diff >= 0 ? "+" : "";
  const text = `${sign}${pct}%`;
  if (metric.higherIsBetter === null) return { text, color: "text-muted-foreground", status: "—" };
  const favorable = (diff > 0 && metric.higherIsBetter) || (diff < 0 && !metric.higherIsBetter);
  const status = diff > 0 ? "▲ Above" : diff < 0 ? "▼ Below" : "— At par";
  return { text, color: favorable ? "text-green-600 font-semibold" : "text-red-600 font-semibold", status };
}

interface CompsTabProps {
  comps: Comp[];
  fields: ExtractedField[];
  onRefetch: () => Promise<void>;
}

export function CompsTab({ comps, fields, onRefetch }: CompsTabProps) {
  const [refetching, setRefetching] = useState(false);

  async function handleRefetch() {
    setRefetching(true);
    try {
      await onRefetch();
    } finally {
      setRefetching(false);
    }
  }

  const ranges = computeRanges(comps);
  const subjectMetrics: Partial<Record<keyof Comp, number>> = {};
  for (const metric of GAP_METRICS) {
    const val = getSubjectValue(metric, fields);
    if (val !== null) subjectMetrics[metric.key] = val;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold">Comparable Properties</h3>
          <p className="text-sm text-muted-foreground">
            {comps.length} comp{comps.length !== 1 ? "s" : ""} found
          </p>
        </div>
        <Button variant="outline" onClick={handleRefetch} disabled={refetching}>
          {refetching ? "Fetching..." : "Re-fetch Comps"}
        </Button>
      </div>

      {comps.length === 0 ? (
        <div className="text-muted-foreground text-sm py-8 text-center">
          No comparable properties found yet.
        </div>
      ) : (
        <>
          {/* Gap Analysis Table */}
          <div>
            <h4 className="text-sm font-semibold mb-2">Gap Analysis</h4>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Metric</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead>Comp Avg</TableHead>
                  <TableHead>Gap</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {GAP_METRICS.map((metric) => {
                  const compValues = comps
                    .map((c) => c[metric.key] as number | null)
                    .filter((v): v is number => v !== null);
                  const compAvg = avg(compValues);
                  const subjectVal = subjectMetrics[metric.key] ?? null;
                  const { text: gapText, color: gapColor, status } = gapLabel(subjectVal, compAvg, metric);

                  if (compAvg === null) return null;

                  return (
                    <TableRow key={metric.key as string}>
                      <TableCell className="font-medium">{metric.label}</TableCell>
                      <TableCell>
                        {subjectVal !== null ? (
                          metric.format(subjectVal)
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>{metric.format(compAvg)}</TableCell>
                      <TableCell className={gapColor}>{gapText}</TableCell>
                      <TableCell className={gapColor}>{status}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>

          {/* Comp Cards Grid */}
          <div>
            <h4 className="text-sm font-semibold mb-2">Individual Comparables</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {comps.map((comp) => (
                <CompCard
                  key={comp.id}
                  comp={comp}
                  subjectMetrics={subjectMetrics}
                  ranges={ranges}
                />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
