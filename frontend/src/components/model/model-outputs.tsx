"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ModelResult } from "@/interfaces/api";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

interface ModelOutputsProps {
  result: ModelResult | null;
}

export function ModelOutputs({ result }: ModelOutputsProps) {
  if (!result) {
    return (
      <p className="text-muted-foreground text-sm">
        No model result yet. Set assumptions and click &quot;Compute Model&quot;
        to generate outputs.
      </p>
    );
  }

  const cards = [
    {
      title: "NOI (Stabilized)",
      value: formatCurrency(result.noi_stabilized),
      color: "text-blue-700",
    },
    {
      title: "Exit Value",
      value: formatCurrency(result.exit_value),
      color: "text-green-700",
    },
    {
      title: "Total Cost",
      value: formatCurrency(result.total_cost),
      color: "text-orange-700",
    },
    {
      title: "Profit",
      value: formatCurrency(result.profit),
      color: result.profit >= 0 ? "text-green-700" : "text-red-700",
    },
    {
      title: "Profit Margin",
      value: formatPercent(result.profit_margin_pct),
      color:
        result.profit_margin_pct >= 0 ? "text-green-700" : "text-red-700",
    },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card) => (
          <Card key={card.title}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {card.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className={`text-2xl font-bold ${card.color}`}>
                {card.value}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <p className="text-xs text-muted-foreground">
        Computed at{" "}
        {new Date(result.computed_at).toLocaleString()}
      </p>
    </div>
  );
}
