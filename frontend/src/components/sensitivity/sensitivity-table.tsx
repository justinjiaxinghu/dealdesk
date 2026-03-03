"use client";

import type { SensitivityResponse } from "@/interfaces/api";

const METRIC_LABELS: Record<string, string> = {
  irr: "IRR",
  equity_multiple: "Equity Multiple",
  cash_on_cash_yr1: "Cash-on-Cash (Yr 1)",
  cap_rate_on_cost: "Cap Rate on Cost",
};

const AXIS_LABELS: Record<string, string> = {
  purchase_price: "Purchase Price",
  exit_cap_rate: "Exit Cap Rate",
  ltv: "LTV",
  base_occupancy_rate: "Occupancy Rate",
  base_gross_revenue: "Gross Revenue",
  sofr_rate: "SOFR Rate",
  spread: "Spread",
};

function formatCell(metric: string, value: number | null): string {
  if (value === null || value === undefined) return "—";
  if (metric === "irr" || metric === "cash_on_cash_yr1" || metric === "cap_rate_on_cost") {
    return `${(value * 100).toFixed(2)}%`;
  }
  if (metric === "equity_multiple") {
    return `${value.toFixed(2)}x`;
  }
  return value.toFixed(2);
}

function cellColor(metric: string, value: number | null, target: number | null): string {
  if (value === null || target === null) return "";
  const isGood =
    metric === "equity_multiple" || metric === "irr" || metric === "cash_on_cash_yr1"
      ? value >= target
      : value >= target;
  return isGood ? "bg-green-50 text-green-800" : "bg-red-50 text-red-700";
}

interface SensitivityTableProps {
  metric: string;
  response: SensitivityResponse;
  target?: number | null;
}

export function SensitivityTable({ metric, response, target }: SensitivityTableProps) {
  const grid = response.grids[metric];
  if (!grid) return null;

  const xVals = response.x_axis.values;
  const yVals = response.y_axis.values;
  const xLabel = AXIS_LABELS[response.x_axis.key] ?? response.x_axis.key;
  const yLabel = AXIS_LABELS[response.y_axis.key] ?? response.y_axis.key;

  return (
    <div>
      <h3 className="text-sm font-semibold mb-2">{METRIC_LABELS[metric] ?? metric}</h3>
      <div className="overflow-x-auto">
        <table className="text-xs border-collapse">
          <thead>
            <tr>
              <th className="border p-1 bg-muted text-left font-medium min-w-24">
                {yLabel} \ {xLabel}
              </th>
              {xVals.map((x) => (
                <th key={x} className="border p-1 bg-muted text-right font-medium min-w-20">
                  {x.toLocaleString()}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {yVals.map((y, yi) => (
              <tr key={y}>
                <td className="border p-1 bg-muted font-medium text-right">{y.toLocaleString()}</td>
                {(grid[yi] ?? []).map((val, xi) => (
                  <td
                    key={xi}
                    className={`border p-1 text-right tabular-nums ${cellColor(metric, val, target ?? null)}`}
                  >
                    {formatCell(metric, val)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
