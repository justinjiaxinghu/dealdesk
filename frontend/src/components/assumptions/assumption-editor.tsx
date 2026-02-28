"use client";

import { Badge } from "@/components/ui/badge";
import type { Assumption } from "@/interfaces/api";

function sourceTypeBadge(sourceType: string) {
  switch (sourceType.toLowerCase()) {
    case "extracted":
      return (
        <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">
          Extracted
        </Badge>
      );
    case "benchmark":
      return (
        <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100">
          Benchmark
        </Badge>
      );
    default:
      return <Badge variant="outline">{sourceType}</Badge>;
  }
}

interface AssumptionEditorProps {
  assumptions: Assumption[];
}

export function AssumptionEditor({
  assumptions,
}: AssumptionEditorProps) {
  if (assumptions.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No assumptions yet. AI benchmarks will be generated automatically after
        document processing completes.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left p-2 font-medium">Key</th>
            <th className="text-left p-2 font-medium">Value</th>
            <th className="text-left p-2 font-medium">Unit</th>
            <th className="text-left p-2 font-medium">Min</th>
            <th className="text-left p-2 font-medium">Max</th>
            <th className="text-left p-2 font-medium">Source</th>
            <th className="text-left p-2 font-medium">Notes</th>
          </tr>
        </thead>
        <tbody>
          {assumptions.map((a) => (
            <tr key={a.id} className="border-b">
              <td className="p-2 font-medium whitespace-nowrap">{a.key}</td>
              <td className="p-2">
                {a.value_number?.toLocaleString() ?? "-"}
              </td>
              <td className="p-2">{a.unit ?? "-"}</td>
              <td className="p-2">
                {a.range_min?.toLocaleString() ?? "-"}
              </td>
              <td className="p-2">
                {a.range_max?.toLocaleString() ?? "-"}
              </td>
              <td className="p-2">{sourceTypeBadge(a.source_type)}</td>
              <td className="p-2 text-muted-foreground">
                {a.notes ?? "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
