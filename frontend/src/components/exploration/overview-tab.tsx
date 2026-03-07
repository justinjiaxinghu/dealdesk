"use client";

import type { Deal } from "@/interfaces/api";
import type { PropertyData } from "./property-card";
import { PropertyCard } from "./property-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface OverviewTabProps {
  deal?: Deal | null;
  properties: PropertyData[];
  onSelectProperty: (index: number) => void;
}

function MetricCard({
  label,
  value,
  subjectValue,
}: {
  label: string;
  value: string | null;
  subjectValue?: string | null;
}) {
  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="text-xs text-muted-foreground font-medium">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="text-lg font-semibold">{value ?? "-"}</div>
        {subjectValue && (
          <div className="text-xs text-muted-foreground mt-0.5">
            Subject: {subjectValue}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function computeAvg(
  properties: PropertyData[],
  key: keyof PropertyData
): number | null {
  const values = properties
    .map((p) => p[key])
    .filter((v): v is number => typeof v === "number");
  if (values.length === 0) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function fmtPct(v: number | null): string | null {
  return v != null ? `${(v * 100).toFixed(1)}%` : null;
}

function fmtCurrency(v: number | null): string | null {
  if (v == null) return null;
  if (Math.abs(v) >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (Math.abs(v) >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

export function OverviewTab({
  deal,
  properties,
  onSelectProperty,
}: OverviewTabProps) {
  const avgCapRate = computeAvg(properties, "cap_rate");
  const avgNoi = computeAvg(properties, "noi");
  const avgRentPsf = computeAvg(properties, "rent_per_sqft");
  const avgSalePrice = computeAvg(properties, "sale_price");

  return (
    <div className="space-y-6">
      {/* Metric comparison cards */}
      {properties.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-3">
            Market Comparison ({properties.length} properties)
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard
              label="Avg Cap Rate"
              value={fmtPct(avgCapRate)}
              subjectValue={deal ? undefined : undefined}
            />
            <MetricCard label="Avg NOI" value={fmtCurrency(avgNoi)} />
            <MetricCard
              label="Avg Rent/SF"
              value={
                avgRentPsf != null ? `$${avgRentPsf.toFixed(2)}` : null
              }
            />
            <MetricCard
              label="Avg Sale Price"
              value={fmtCurrency(avgSalePrice)}
            />
          </div>
        </div>
      )}

      {/* Property card grid */}
      {properties.length > 0 ? (
        <div>
          <h3 className="text-sm font-semibold mb-3">Discovered Properties</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {properties.map((prop, index) => (
              <PropertyCard
                key={index}
                property={prop}
                onSelect={() => onSelectProperty(index)}
              />
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-muted-foreground text-sm">
          {deal
            ? "Search for comparable properties to see results here."
            : "Select or create a deal to get started."}
        </div>
      )}
    </div>
  );
}
