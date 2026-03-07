"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface PropertyData {
  address: string;
  property_type?: string;
  cap_rate?: number;
  rent_per_sqft?: number;
  sale_price?: number;
  noi?: number;
  [key: string]: unknown;
}

interface PropertyCardProps {
  property: PropertyData;
  onSelect: () => void;
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`;
  }
  return `$${value.toFixed(0)}`;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function PropertyCard({ property, onSelect }: PropertyCardProps) {
  const metrics = [
    property.cap_rate != null && {
      label: "Cap Rate",
      value: formatPercent(property.cap_rate),
    },
    property.rent_per_sqft != null && {
      label: "Rent/SF",
      value: `$${property.rent_per_sqft.toFixed(2)}`,
    },
    property.sale_price != null && {
      label: "Sale Price",
      value: formatCurrency(property.sale_price),
    },
    property.noi != null && {
      label: "NOI",
      value: formatCurrency(property.noi),
    },
  ].filter(Boolean) as { label: string; value: string }[];

  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={onSelect}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-sm leading-tight">
            {property.address}
          </CardTitle>
          {property.property_type && (
            <Badge variant="secondary" className="text-xs shrink-0">
              {property.property_type}
            </Badge>
          )}
        </div>
      </CardHeader>
      {metrics.length > 0 && (
        <CardContent className="pt-0">
          <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
            {metrics.map((m) => (
              <div key={m.label} className="flex justify-between text-xs">
                <span className="text-muted-foreground">{m.label}</span>
                <span className="font-medium">{m.value}</span>
              </div>
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  );
}
