"use client";

import type { FieldValidation } from "@/interfaces/api";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { SearchStepTree } from "./search-step-tree";

const STATUS_CONFIG: Record<
  string,
  { label: string; variant: "default" | "secondary" | "destructive" }
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

function markdownLinksToHtml(text: string): string {
  return text.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">$1</a>'
  );
}

interface ValidationDetailModalProps {
  validation: FieldValidation | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ValidationDetailModal({
  validation,
  open,
  onOpenChange,
}: ValidationDetailModalProps) {
  if (!validation) return null;

  const config =
    STATUS_CONFIG[validation.status] ?? STATUS_CONFIG.insufficient_data;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <span>{formatFieldKey(validation.field_key)}</span>
            <Badge variant={config.variant}>{config.label}</Badge>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-5">
          {/* Values comparison */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-md border p-3">
              <div className="text-xs text-muted-foreground mb-1">OM Value</div>
              <div className="text-lg font-semibold">
                {validation.om_value !== null ? validation.om_value : "-"}
              </div>
            </div>
            <div className="rounded-md border p-3">
              <div className="text-xs text-muted-foreground mb-1">
                Market Value
              </div>
              <div className="text-lg font-semibold">
                {validation.market_value !== null
                  ? validation.market_value
                  : "-"}
              </div>
            </div>
          </div>

          {/* Confidence */}
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">Confidence:</span>
            <span className="font-medium">
              {(validation.confidence * 100).toFixed(0)}%
            </span>
          </div>

          {/* Explanation */}
          <div>
            <h4 className="text-sm font-semibold mb-2">Explanation</h4>
            <div
              className="prose prose-sm max-w-none text-sm"
              dangerouslySetInnerHTML={{
                __html: markdownLinksToHtml(validation.explanation),
              }}
            />
          </div>

          {/* Search steps */}
          <div>
            <h4 className="text-sm font-semibold mb-2">Research Steps</h4>
            <SearchStepTree steps={validation.search_steps ?? []} />
          </div>

          {/* Sources */}
          {validation.sources.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2">
                Sources ({validation.sources.length})
              </h4>
              <div className="space-y-1.5">
                {validation.sources.map((s, i) => (
                  <a
                    key={i}
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-xs text-blue-600 hover:underline"
                    title={s.snippet}
                  >
                    [{i + 1}] {s.title || s.url}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
