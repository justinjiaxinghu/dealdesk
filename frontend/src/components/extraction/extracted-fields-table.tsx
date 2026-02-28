"use client";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ExtractedField, MarketTable } from "@/interfaces/api";

function confidenceBadge(confidence: number) {
  if (confidence >= 0.8) {
    return (
      <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
        {(confidence * 100).toFixed(0)}%
      </Badge>
    );
  }
  if (confidence >= 0.5) {
    return (
      <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">
        {(confidence * 100).toFixed(0)}%
      </Badge>
    );
  }
  return (
    <Badge className="bg-red-100 text-red-800 hover:bg-red-100">
      {(confidence * 100).toFixed(0)}%
    </Badge>
  );
}

interface ExtractedFieldsTableProps {
  fields: ExtractedField[];
  tables: MarketTable[];
}

export function ExtractedFieldsTable({
  fields,
  tables,
}: ExtractedFieldsTableProps) {
  return (
    <div className="space-y-8">
      {/* Extracted Fields */}
      <div>
        <h3 className="text-lg font-semibold mb-3">Extracted Fields</h3>
        {fields.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No extracted fields yet. Upload and process a document first.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Field</TableHead>
                <TableHead>Value</TableHead>
                <TableHead>Unit</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Page</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fields.map((field) => (
                <TableRow key={field.id}>
                  <TableCell className="font-medium">
                    {field.field_key}
                  </TableCell>
                  <TableCell>
                    {field.value_text ??
                      field.value_number?.toLocaleString() ??
                      "-"}
                  </TableCell>
                  <TableCell>{field.unit ?? "-"}</TableCell>
                  <TableCell>{confidenceBadge(field.confidence)}</TableCell>
                  <TableCell>{field.source_page ?? "-"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Market Tables */}
      {tables.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Market Tables</h3>
          {tables.map((mt) => (
            <div key={mt.id} className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <span className="font-medium text-sm">{mt.table_type}</span>
                {confidenceBadge(mt.confidence)}
                {mt.source_page !== null && (
                  <span className="text-xs text-muted-foreground">
                    Page {mt.source_page}
                  </span>
                )}
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    {mt.headers.map((h, i) => (
                      <TableHead key={i}>{h}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mt.rows.map((row, ri) => (
                    <TableRow key={ri}>
                      {row.map((cell, ci) => (
                        <TableCell key={ci}>{cell}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
