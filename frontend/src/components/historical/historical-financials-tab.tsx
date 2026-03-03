"use client";

import type { HistoricalFinancial } from "@/interfaces/api";

const METRIC_LABELS: Record<string, string> = {
  gross_revenue: "Gross Revenue",
  effective_gross_income: "Effective Gross Income",
  total_operating_expenses: "Total OpEx",
  noi: "NOI",
  expense_ratio: "Expense Ratio",
  occupancy_rate: "Occupancy Rate",
  revenue_per_unit: "Revenue / Unit",
  opex_per_unit: "OpEx / Unit",
  total_units: "Total Units",
  net_rentable_area: "Net Rentable Area",
};

function formatValue(value: number, unit: string | null): string {
  if (unit === "%") {
    return `${(value * 100).toFixed(1)}%`;
  }
  if (unit === "$") {
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
    if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
    return `$${value.toFixed(0)}`;
  }
  return `${value.toLocaleString()}${unit ? ` ${unit}` : ""}`;
}

function trendArrow(values: number[]): string {
  if (values.length < 2) return "";
  const delta = values[values.length - 1] - values[0];
  if (delta > 0) return " ↑";
  if (delta < 0) return " ↓";
  return " →";
}

interface HistoricalFinancialsTabProps {
  items: HistoricalFinancial[];
}

export function HistoricalFinancialsTab({ items }: HistoricalFinancialsTabProps) {
  if (items.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No historical financials extracted yet.
      </p>
    );
  }

  const periods = [...new Set(items.map((i) => i.period_label))].sort();
  const metrics = [...new Set(items.map((i) => i.metric_key))];

  const lookup: Record<string, Record<string, HistoricalFinancial>> = {};
  for (const item of items) {
    lookup[item.metric_key] ??= {};
    lookup[item.metric_key][item.period_label] = item;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left p-2 font-medium w-48">Metric</th>
            {periods.map((p) => (
              <th key={p} className="text-right p-2 font-medium">{p}</th>
            ))}
            <th className="text-right p-2 font-medium w-8">Trend</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => {
            const row = lookup[metric] ?? {};
            const values = periods
              .map((p) => row[p]?.value)
              .filter((v): v is number => v !== undefined);
            return (
              <tr key={metric} className="border-b hover:bg-muted/30">
                <td className="p-2 font-medium">
                  {METRIC_LABELS[metric] ?? metric}
                </td>
                {periods.map((p) => {
                  const item = row[p];
                  return (
                    <td key={p} className="p-2 text-right tabular-nums">
                      {item ? formatValue(item.value, item.unit) : "—"}
                    </td>
                  );
                })}
                <td className="p-2 text-right text-muted-foreground">
                  {trendArrow(values)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
