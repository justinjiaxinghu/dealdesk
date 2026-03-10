"use client";

import { Button } from "@/components/ui/button";

interface ComparisonToggleProps {
  view: "table" | "chart";
  onViewChange: (view: "table" | "chart") => void;
}

export function ComparisonToggle({ view, onViewChange }: ComparisonToggleProps) {
  return (
    <div className="inline-flex items-center rounded-lg border p-0.5">
      <Button
        variant={view === "table" ? "secondary" : "ghost"}
        size="xs"
        onClick={() => onViewChange("table")}
      >
        Table
      </Button>
      <Button
        variant={view === "chart" ? "secondary" : "ghost"}
        size="xs"
        onClick={() => onViewChange("chart")}
      >
        Chart
      </Button>
    </div>
  );
}
