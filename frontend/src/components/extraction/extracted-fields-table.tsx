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
import type { ExtractedField } from "@/interfaces/api";

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
}

export function ExtractedFieldsTable({
  fields,
}: ExtractedFieldsTableProps) {
  if (fields.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No extracted fields yet. Upload and process a document first.
      </p>
    );
  }

  return (
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
  );
}
