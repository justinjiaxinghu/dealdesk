"use client";

import { useState } from "react";
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
import { SearchStepTree } from "./search-step-tree";

const STATUS_CONFIG: Record<
  string,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
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
  const [expandedId, setExpandedId] = useState<string | null>(null);

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
            const config =
              STATUS_CONFIG[v.status] ?? STATUS_CONFIG.insufficient_data;
            const isExpanded = expandedId === v.id;
            return (
              <>
                <TableRow
                  key={v.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() =>
                    setExpandedId(isExpanded ? null : v.id)
                  }
                >
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`text-xs transition-transform ${isExpanded ? "rotate-90" : ""}`}
                      >
                        {"\u25B6"}
                      </span>
                      {formatFieldKey(v.field_key)}
                    </div>
                  </TableCell>
                  <TableCell>
                    {v.om_value !== null ? v.om_value : "-"}
                  </TableCell>
                  <TableCell>
                    {v.market_value !== null ? v.market_value : "-"}
                  </TableCell>
                  <TableCell>
                    <Badge variant={config.variant}>{config.label}</Badge>
                  </TableCell>
                  <TableCell className="text-sm">
                    <div
                      className="prose prose-sm max-w-none line-clamp-2"
                      dangerouslySetInnerHTML={{
                        __html: markdownLinksToHtml(v.explanation),
                      }}
                    />
                  </TableCell>
                </TableRow>
                {isExpanded && (
                  <TableRow key={`${v.id}-detail`}>
                    <TableCell colSpan={5} className="bg-muted/30 p-6">
                      <div className="space-y-4">
                        {/* Full explanation */}
                        <div>
                          <h4 className="text-sm font-semibold mb-2">
                            Explanation
                          </h4>
                          <div
                            className="prose prose-sm max-w-none text-sm"
                            dangerouslySetInnerHTML={{
                              __html: markdownLinksToHtml(v.explanation),
                            }}
                          />
                        </div>

                        {/* Search step tree */}
                        <div>
                          <h4 className="text-sm font-semibold mb-2">
                            Research Steps
                          </h4>
                          <SearchStepTree
                            steps={v.search_steps ?? []}
                          />
                        </div>

                        {/* Sources */}
                        {v.sources.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold mb-2">
                              Sources ({v.sources.length})
                            </h4>
                            <div className="space-y-1">
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
                          </div>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

function markdownLinksToHtml(text: string): string {
  return text.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">$1</a>',
  );
}
