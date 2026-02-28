"use client";

import { Badge } from "@/components/ui/badge";
import type { Document } from "@/interfaces/api";

function statusColor(status: string): string {
  switch (status.toLowerCase()) {
    case "completed":
    case "done":
      return "bg-green-100 text-green-800";
    case "running":
    case "in_progress":
    case "processing":
      return "bg-blue-100 text-blue-800";
    case "pending":
    case "queued":
      return "bg-gray-100 text-gray-600";
    case "failed":
    case "error":
      return "bg-red-100 text-red-800";
    default:
      return "bg-gray-100 text-gray-600";
  }
}

interface ProcessingTrackerProps {
  document: Document;
}

export function ProcessingTracker({ document: doc }: ProcessingTrackerProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">{doc.original_filename}</h4>
        <Badge variant="outline" className={statusColor(doc.processing_status)}>
          {doc.processing_status}
        </Badge>
      </div>

      {doc.error_message && (
        <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded">
          {doc.error_message}
        </div>
      )}

      {doc.processing_steps.length > 0 && (
        <div className="space-y-1">
          {doc.processing_steps.map((step, i) => (
            <div
              key={`${step.name}-${i}`}
              className="flex items-center gap-3 text-sm"
            >
              <span
                className={`inline-block w-2 h-2 rounded-full ${
                  step.status === "completed"
                    ? "bg-green-500"
                    : step.status === "running"
                      ? "bg-blue-500 animate-pulse"
                      : step.status === "failed"
                        ? "bg-red-500"
                        : "bg-gray-300"
                }`}
              />
              <span className="font-medium">{step.name}</span>
              <span className="text-muted-foreground">{step.detail}</span>
            </div>
          ))}
        </div>
      )}

      {doc.page_count !== null && (
        <p className="text-xs text-muted-foreground">
          {doc.page_count} page{doc.page_count !== 1 ? "s" : ""}
        </p>
      )}
    </div>
  );
}
