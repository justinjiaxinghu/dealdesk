"use client";

import { useState } from "react";
import type {
  Assumption,
  Deal,
  Document,
  ExtractedField,
  FieldValidation,
  HistoricalFinancial,
} from "@/interfaces/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ValidationDetailModal } from "@/components/validation/validation-detail-modal";

interface DealSidebarProps {
  deal: Deal | null;
  documents: Document[];
  extractedFields: ExtractedField[];
  validations: FieldValidation[];
  assumptions: Assumption[];
  historicalFinancials?: HistoricalFinancial[];
  loading?: boolean;
  onExport?: () => void;
  pipelineStep?: string | null;
  pipelineDetail?: string | null;
}

function ChevronIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      className={`w-4 h-4 transition-transform ${expanded ? "rotate-90" : ""}`}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 5l7 7-7 7"
      />
    </svg>
  );
}

function Spinner() {
  return (
    <svg
      className="w-3.5 h-3.5 animate-spin text-blue-600"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      className="w-3.5 h-3.5 text-green-600"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={3}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
}

function SidebarSection({
  title,
  children,
  defaultExpanded = true,
  status,
}: {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  status?: "loading" | "done" | null;
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <div className="border-b last:border-b-0">
      <button
        className="flex items-center justify-between w-full px-4 py-2.5 text-sm font-medium hover:bg-muted/50 transition-colors"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex items-center gap-2">
          <ChevronIcon expanded={expanded} />
          <span>{title}</span>
        </div>
        {status === "loading" && <Spinner />}
        {status === "done" && <CheckIcon />}
      </button>
      {expanded && <div className="px-4 pb-3">{children}</div>}
    </div>
  );
}

function formatFieldKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/Psf/g, "PSF")
    .replace(/Pct/g, "%");
}

const VALIDATION_STATUS_VARIANT: Record<
  string,
  "default" | "secondary" | "destructive"
> = {
  within_range: "default",
  above_market: "destructive",
  below_market: "destructive",
  suspicious: "destructive",
  insufficient_data: "secondary",
};

export function DealSidebar({
  deal,
  documents,
  extractedFields,
  validations,
  assumptions,
  historicalFinancials = [],
  loading = false,
  onExport,
  pipelineStep,
  pipelineDetail,
}: DealSidebarProps) {
  const [selectedValidation, setSelectedValidation] =
    useState<FieldValidation | null>(null);

  if (loading && !deal) {
    return (
      <aside className="w-[350px] shrink-0 border-r bg-card overflow-y-auto">
        <div className="flex items-center justify-center h-full">
          <Spinner />
          <span className="ml-2 text-sm text-muted-foreground">
            Loading deal...
          </span>
        </div>
      </aside>
    );
  }

  if (!deal) {
    return (
      <aside className="w-[350px] shrink-0 border-r bg-card overflow-y-auto">
        <div className="flex items-center justify-center h-full text-sm text-muted-foreground p-4">
          No deal selected.
        </div>
      </aside>
    );
  }

  const isProcessing = documents.some(
    (d) => d.processing_status === "processing"
  );
  const hasFields = extractedFields.length > 0;
  const hasValidations = validations.length > 0;
  const hasAssumptions = assumptions.length > 0;
  const hasFinancials = historicalFinancials.length > 0;

  const firstDoc = documents[0];
  const pdfUrl = firstDoc
    ? `${process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/v1"}/deals/${deal.id}/documents/${firstDoc.id}/pdf`
    : null;

  // Group assumptions by group field
  const assumptionGroups = assumptions.reduce<Record<string, Assumption[]>>(
    (acc, a) => {
      const group = a.group || "Other";
      if (!acc[group]) acc[group] = [];
      acc[group].push(a);
      return acc;
    },
    {}
  );

  return (
    <aside className="w-[350px] shrink-0 border-r bg-card overflow-y-auto flex flex-col">
      {/* Deal Summary - always visible, not collapsible */}
      <div className="px-4 py-4 border-b">
        <div className="space-y-1.5 text-sm">
          <div className="flex items-start justify-between gap-2">
            <div className="font-semibold text-base">{deal.name}</div>
            {isProcessing && <Spinner />}
            {!isProcessing && hasFields && <CheckIcon />}
          </div>
          <div className="text-muted-foreground">{deal.address}</div>
          <div className="text-muted-foreground">
            {deal.city}, {deal.state}
          </div>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="secondary">{deal.property_type}</Badge>
            {deal.square_feet && (
              <span className="text-xs text-muted-foreground">
                {deal.square_feet.toLocaleString()} SF
              </span>
            )}
          </div>
          {/* View PDF button */}
          {pdfUrl && (
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 mt-2 text-xs text-blue-600 hover:text-blue-800 hover:underline transition-colors"
            >
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
              View PDF
              {firstDoc && (
                <span className="text-muted-foreground">
                  ({firstDoc.original_filename})
                </span>
              )}
            </a>
          )}
        </div>
      </div>

      {/* Pipeline progress banner */}
      {pipelineStep && (
        <div className="px-4 py-3 border-b bg-blue-50 dark:bg-blue-950/30">
          <div className="flex items-center gap-2 text-sm">
            <Spinner />
            <div>
              <div className="font-medium text-blue-700 dark:text-blue-400 capitalize">
                {pipelineStep === "extract" ? "Extracting" :
                 pipelineStep === "historical" ? "Historical Financials" :
                 pipelineStep === "assumptions" ? "Generating Benchmarks" :
                 pipelineStep === "validate" ? "Validating" :
                 pipelineStep === "comps" ? "Finding Comps" : pipelineStep}
              </div>
              {pipelineDetail && (
                <div className="text-xs text-muted-foreground">{pipelineDetail}</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Extraction */}
      <SidebarSection
        title={`Extraction (${extractedFields.length})`}
        defaultExpanded={false}
        status={isProcessing ? "loading" : hasFields ? "done" : null}
      >
        {extractedFields.length > 0 ? (
          <div className="space-y-1">
            {extractedFields.slice(0, 10).map((f) => (
              <div
                key={f.id}
                className="flex justify-between text-xs gap-2"
              >
                <span className="text-muted-foreground truncate">
                  {formatFieldKey(f.field_key)}
                </span>
                <span className="font-medium shrink-0">
                  {f.value_number != null
                    ? f.value_number
                    : f.value_text ?? "-"}
                  {f.unit ? ` ${f.unit}` : ""}
                </span>
              </div>
            ))}
            {extractedFields.length > 10 && (
              <div className="text-xs text-muted-foreground">
                +{extractedFields.length - 10} more fields
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            No extracted fields yet.
          </p>
        )}
      </SidebarSection>

      {/* Validation */}
      <SidebarSection
        title={`Validation (${validations.length})`}
        defaultExpanded={false}
        status={hasValidations ? "done" : null}
      >
        {validations.length > 0 ? (
          <div className="space-y-1.5">
            {validations.map((v) => (
              <button
                key={v.id}
                className="flex items-center justify-between text-xs gap-2 w-full text-left rounded px-1 py-0.5 hover:bg-muted/50 transition-colors cursor-pointer"
                onClick={() => setSelectedValidation(v)}
              >
                <span className="truncate">
                  {formatFieldKey(v.field_key)}
                </span>
                <Badge
                  variant={
                    VALIDATION_STATUS_VARIANT[v.status] ?? "secondary"
                  }
                  className="text-[10px] shrink-0"
                >
                  {v.status.replace(/_/g, " ")}
                </Badge>
              </button>
            ))}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            No validation results yet.
          </p>
        )}
      </SidebarSection>

      {/* Assumptions */}
      <SidebarSection
        title={`Assumptions (${assumptions.length})`}
        defaultExpanded={false}
        status={hasAssumptions ? "done" : null}
      >
        {hasAssumptions ? (
          <div className="space-y-2">
            {Object.entries(assumptionGroups).map(([group, items]) => (
              <div key={group}>
                <div className="text-xs font-medium text-muted-foreground mb-1">
                  {group}
                </div>
                {items.slice(0, 5).map((a) => (
                  <div
                    key={a.id}
                    className="flex justify-between text-xs gap-2"
                  >
                    <span className="text-muted-foreground truncate">
                      {formatFieldKey(a.key)}
                    </span>
                    <span className="font-medium shrink-0">
                      {a.value_number != null ? a.value_number : "-"}
                      {a.unit ? ` ${a.unit}` : ""}
                    </span>
                  </div>
                ))}
                {items.length > 5 && (
                  <div className="text-xs text-muted-foreground">
                    +{items.length - 5} more
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            No assumptions generated yet.
          </p>
        )}
      </SidebarSection>

      {/* Financials */}
      <SidebarSection
        title={`Financials (${historicalFinancials.length})`}
        defaultExpanded={false}
        status={hasFinancials ? "done" : null}
      >
        {hasFinancials ? (
          <div className="space-y-1">
            {historicalFinancials.slice(0, 8).map((hf) => (
              <div
                key={hf.id}
                className="flex justify-between text-xs gap-2"
              >
                <span className="text-muted-foreground truncate">
                  {hf.period_label} - {formatFieldKey(hf.metric_key)}
                </span>
                <span className="font-medium shrink-0">
                  {hf.value.toLocaleString()}
                  {hf.unit ? ` ${hf.unit}` : ""}
                </span>
              </div>
            ))}
            {historicalFinancials.length > 8 && (
              <div className="text-xs text-muted-foreground">
                +{historicalFinancials.length - 8} more entries
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            No financial data yet.
          </p>
        )}
      </SidebarSection>

      {/* Export button */}
      <div className="mt-auto p-4 border-t">
        <Button
          className="w-full"
          onClick={onExport}
          disabled={!hasAssumptions}
        >
          Export XLSX
        </Button>
      </div>

      {/* Validation detail modal */}
      <ValidationDetailModal
        validation={selectedValidation}
        open={selectedValidation !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedValidation(null);
        }}
      />
    </aside>
  );
}
