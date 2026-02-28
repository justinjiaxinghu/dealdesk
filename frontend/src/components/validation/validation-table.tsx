"use client";

import type { FieldValidation } from "@/interfaces/api";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const STATUS_CONFIG: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  within_range: { label: "In Range", variant: "default" },
  above_market: { label: "Above Market", variant: "destructive" },
  below_market: { label: "Below Market", variant: "destructive" },
  suspicious: { label: "Suspicious", variant: "destructive" },
  insufficient_data: { label: "Insufficient Data", variant: "secondary" },
};

function formatFieldKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/Psf/g, "PSF")
    .replace(/Pct/g, "%");
}

interface ValidationTableProps {
  validations: FieldValidation[];
}

export function ValidationTable({ validations }: ValidationTableProps) {
  if (validations.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No validation results yet.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Field</TableHead>
            <TableHead>OM Value</TableHead>
            <TableHead>Market Value</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-[40%]">Explanation</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {validations.map((v) => {
            const config = STATUS_CONFIG[v.status] ?? STATUS_CONFIG.insufficient_data;
            return (
              <TableRow key={v.id}>
                <TableCell className="font-medium">
                  {formatFieldKey(v.field_key)}
                </TableCell>
                <TableCell>{v.om_value !== null ? v.om_value : "-"}</TableCell>
                <TableCell>
                  {v.market_value !== null ? v.market_value : "-"}
                </TableCell>
                <TableCell>
                  <Badge variant={config.variant}>{config.label}</Badge>
                </TableCell>
                <TableCell className="text-sm">
                  <div
                    className="prose prose-sm max-w-none"
                    dangerouslySetInnerHTML={{ __html: markdownLinksToHtml(v.explanation) }}
                  />
                  {v.sources.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {v.sources.map((s, i) => (
                        <a
                          key={i}
                          href={s.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block text-xs text-blue-600 hover:underline truncate"
                          title={s.snippet}
                        >
                          [{i + 1}] {s.title || s.url}
                        </a>
                      ))}
                    </div>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

function markdownLinksToHtml(text: string): string {
  // Convert markdown links [text](url) to <a> tags
  return text.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">$1</a>',
  );
}
