"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { SensitivityTable } from "./sensitivity-table";
import { financialModelService } from "@/services/financial-model.service";
import type { SensitivityResponse } from "@/interfaces/api";

const DEFAULT_CONFIGS = [
  {
    metrics: ["irr", "equity_multiple"] as const,
    x_axis: { key: "purchase_price", values: [900_000, 950_000, 1_000_000, 1_050_000, 1_100_000] },
    y_axis: { key: "exit_cap_rate", values: [0.05, 0.055, 0.06, 0.065, 0.07] },
  },
  {
    metrics: ["cash_on_cash_yr1", "cap_rate_on_cost"] as const,
    x_axis: { key: "base_gross_revenue", values: [85_000, 92_500, 100_000, 107_500, 115_000] },
    y_axis: { key: "sofr_rate", values: [0.03, 0.04, 0.05, 0.06] },
  },
];

interface SensitivityTabProps {
  dealId: string;
}

export function SensitivityTab({ dealId }: SensitivityTabProps) {
  const [results, setResults] = useState<SensitivityResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function recalculate() {
    setLoading(true);
    setError(null);
    try {
      const responses = await Promise.all(
        DEFAULT_CONFIGS.map((cfg) =>
          financialModelService.sensitivity(dealId, {
            x_axis: cfg.x_axis,
            y_axis: cfg.y_axis,
            metrics: [...cfg.metrics],
          })
        )
      );
      setResults(responses);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to compute sensitivity");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Two-way sensitivity tables. Cells turn green when the return meets or exceeds your target.
        </p>
        <Button size="sm" onClick={recalculate} disabled={loading}>
          {loading ? "Calculating..." : "Recalculate"}
        </Button>
      </div>

      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}

      {results.length === 0 && !loading && (
        <p className="text-sm text-muted-foreground">
          Click Recalculate to generate sensitivity tables.
        </p>
      )}

      {results.map((response, i) => (
        <div key={i} className="space-y-4 border rounded-lg p-4">
          {DEFAULT_CONFIGS[i].metrics.map((metric) => (
            <SensitivityTable key={metric} metric={metric} response={response} />
          ))}
        </div>
      ))}
    </div>
  );
}
