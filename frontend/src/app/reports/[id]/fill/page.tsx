"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { reportService } from "@/services/report.service";
import { connectorService } from "@/services/connector.service";
import type { ReportTemplate, ReportJob, Connector } from "@/interfaces/api";

type Phase = "select" | "review";

export default function FillReportPage() {
  const params = useParams();
  const router = useRouter();
  const templateId = params.id as string;

  const [template, setTemplate] = useState<ReportTemplate | null>(null);
  const [job, setJob] = useState<ReportJob | null>(null);
  const [fills, setFills] = useState<Record<string, { rows: string[][] }>>({});
  const [generating, setGenerating] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Phase 1 state
  const [phase, setPhase] = useState<Phase>("select");
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [selectedConnectors, setSelectedConnectors] = useState<Set<string>>(
    new Set(),
  );
  const [prompt, setPrompt] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  // Fetch template, create job, and load connectors on mount
  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        const [tmpl, conns] = await Promise.all([
          reportService.getTemplate(templateId),
          connectorService.list(),
        ]);
        if (cancelled) return;
        setTemplate(tmpl);
        setConnectors(conns);

        // Initialize empty fills for each region
        const initialFills: Record<string, { rows: string[][] }> = {};
        for (const region of tmpl.regions) {
          const rowCount = Math.max(region.row_count, 1);
          const colCount = region.headers.length || 1;
          initialFills[region.region_id] = {
            rows: Array.from({ length: rowCount }, () =>
              Array.from({ length: colCount }, () => ""),
            ),
          };
        }
        setFills(initialFills);

        const newJob = await reportService.createJob(
          templateId,
          `${tmpl.name} - ${new Date().toLocaleDateString()}`,
        );
        if (cancelled) return;
        setJob(newJob);
      } catch (err) {
        console.error("Failed to initialize fill page", err);
        if (!cancelled) setError("Failed to load template.");
      }
    }

    init();
    return () => {
      cancelled = true;
    };
  }, [templateId]);

  const toggleConnector = useCallback((provider: string) => {
    setSelectedConnectors((prev) => {
      const next = new Set(prev);
      if (next.has(provider)) next.delete(provider);
      else next.add(provider);
      return next;
    });
  }, []);

  const handleAiFill = useCallback(async () => {
    if (!job) return;
    setAiLoading(true);
    setError(null);
    try {
      const updated = await reportService.aiFill(
        job.id,
        Array.from(selectedConnectors),
        prompt || undefined,
      );
      setJob(updated);

      // Parse returned fills into local state
      if (updated.fills && template) {
        const parsedFills: Record<string, { rows: string[][] }> = {};
        for (const region of template.regions) {
          const regionFill = updated.fills[region.region_id] as
            | { rows: string[][] }
            | undefined;
          if (regionFill?.rows) {
            parsedFills[region.region_id] = { rows: regionFill.rows };
          } else {
            // Keep existing empty fills if AI didn't return data for this region
            parsedFills[region.region_id] = fills[region.region_id] || {
              rows: Array.from({ length: Math.max(region.row_count, 1) }, () =>
                Array.from({ length: region.headers.length || 1 }, () => ""),
              ),
            };
          }
        }
        setFills(parsedFills);
      }

      setPhase("review");
    } catch (err) {
      console.error("AI fill failed", err);
      setError("AI fill failed. Please try again.");
    } finally {
      setAiLoading(false);
    }
  }, [job, selectedConnectors, prompt, template, fills]);

  const updateCell = useCallback(
    (regionId: string, rowIdx: number, colIdx: number, value: string) => {
      setFills((prev) => {
        const regionFills = prev[regionId];
        if (!regionFills) return prev;
        const newRows = regionFills.rows.map((row) => [...row]);
        newRows[rowIdx][colIdx] = value;
        return { ...prev, [regionId]: { rows: newRows } };
      });
    },
    [],
  );

  const addRow = useCallback(
    (regionId: string) => {
      setFills((prev) => {
        const regionFills = prev[regionId];
        if (!regionFills) return prev;
        const colCount =
          regionFills.rows[0]?.length ||
          template?.regions.find((r) => r.region_id === regionId)?.headers
            .length ||
          1;
        const newRow = Array.from({ length: colCount }, () => "");
        return {
          ...prev,
          [regionId]: { rows: [...regionFills.rows, newRow] },
        };
      });
    },
    [template],
  );

  const saveFills = useCallback(async () => {
    if (!job) return;
    try {
      await reportService.updateFills(job.id, fills);
    } catch (err) {
      console.error("Failed to save fills", err);
    }
  }, [job, fills]);

  const handleGenerate = useCallback(async () => {
    if (!job) return;
    setGenerating(true);
    setError(null);
    try {
      await saveFills();
      const updated = await reportService.generate(job.id);
      setJob(updated);
      setCompleted(true);
    } catch (err) {
      console.error("Report generation failed", err);
      setError("Report generation failed. Please try again.");
    } finally {
      setGenerating(false);
    }
  }, [job, saveFills]);

  // --- Error state (no template loaded) ---
  if (error && !template) {
    return (
      <div className="py-12 text-center">
        <p className="text-destructive mb-4">{error}</p>
        <Button variant="outline" onClick={() => router.push("/reports")}>
          Back to Reports
        </Button>
      </div>
    );
  }

  // --- Loading state ---
  if (!template || !job) {
    return (
      <div className="text-muted-foreground py-12 text-center">
        Loading template...
      </div>
    );
  }

  const regions = template.regions;

  // --- Completed state ---
  if (completed) {
    return (
      <div className="max-w-lg mx-auto py-16 text-center space-y-6">
        <h1 className="text-2xl font-bold">Report Generated</h1>
        <p className="text-muted-foreground">
          Your report has been generated and is ready for download.
        </p>
        <div className="flex items-center justify-center gap-4">
          <a
            href={reportService.downloadUrl(job.id)}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90"
          >
            Download Report
          </a>
          <Button variant="outline" onClick={() => router.push("/reports")}>
            Back to Reports
          </Button>
        </div>
      </div>
    );
  }

  // --- No regions edge case ---
  if (regions.length === 0) {
    return (
      <div className="max-w-lg mx-auto py-16 text-center space-y-6">
        <h1 className="text-2xl font-bold">{template.name}</h1>
        <p className="text-muted-foreground">
          No fillable regions detected in this template.
        </p>
        <Button variant="outline" onClick={() => router.push("/reports")}>
          Back to Reports
        </Button>
      </div>
    );
  }

  const connectorProviders = ["onedrive", "box", "google_drive", "sharepoint"];

  // --- Phase 1: Context Selection ---
  if (phase === "select") {
    return (
      <div className="max-w-2xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold">{template.name}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Configure sources and instructions for AI-powered fill.
          </p>
        </div>

        {/* Select Sources */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            Select Sources
          </h2>
          <div className="flex items-center gap-2 flex-wrap">
            {connectorProviders.map((provider) => {
              const connector = connectors.find(
                (c) => c.provider === provider,
              );
              const isConnected = connector?.status === "connected";
              const isSelected = selectedConnectors.has(provider);
              const label = provider.replace("_", " ").toUpperCase();

              return (
                <button
                  key={provider}
                  type="button"
                  onClick={() => isConnected && toggleConnector(provider)}
                  disabled={!isConnected}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors select-none ${
                    !isConnected
                      ? "opacity-50 cursor-not-allowed border-border text-muted-foreground bg-muted"
                      : isSelected
                        ? "bg-foreground text-background border-foreground cursor-pointer"
                        : "bg-background text-foreground border-border cursor-pointer hover:bg-muted"
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Instructions */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            Instructions
          </h2>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Optional: provide additional context or instructions for the AI..."
            rows={4}
            className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1"
          />
        </div>

        {/* Error */}
        {error && <p className="text-sm text-destructive">{error}</p>}

        {/* Generate button */}
        <div className="flex items-center gap-3">
          <Button onClick={handleAiFill} disabled={aiLoading}>
            {aiLoading ? (
              <span className="flex items-center gap-2">
                <svg
                  className="w-4 h-4 animate-spin"
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
                Generating...
              </span>
            ) : (
              "Generate with AI"
            )}
          </Button>
          <Button variant="outline" onClick={() => router.push("/reports")}>
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  // --- Phase 2: Review & Export ---
  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-24">
      <div>
        <h1 className="text-2xl font-bold">{template.name}</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Review and edit the AI-generated fills, then export.
        </p>
      </div>

      {/* All regions */}
      {regions.map((region) => {
        const regionFills = fills[region.region_id];
        return (
          <div key={region.region_id} className="space-y-3">
            {/* Region header */}
            <div>
              <h2 className="text-lg font-semibold">{region.label}</h2>
              <p className="text-sm text-muted-foreground">
                {region.sheet_or_slide}
              </p>
            </div>

            {/* Editable table */}
            <div className="border rounded-md overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    {region.headers.map((header, colIdx) => (
                      <th
                        key={colIdx}
                        className="px-3 py-2 text-left font-medium text-muted-foreground"
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {regionFills?.rows.map((row, rowIdx) => (
                    <tr key={rowIdx} className="border-b last:border-b-0">
                      {row.map((cellValue, colIdx) => (
                        <td key={colIdx} className="px-2 py-1">
                          <Input
                            value={cellValue}
                            onChange={(e) =>
                              updateCell(
                                region.region_id,
                                rowIdx,
                                colIdx,
                                e.target.value,
                              )
                            }
                            className="h-8 text-sm"
                          />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => addRow(region.region_id)}
            >
              + Add Row
            </Button>
          </div>
        );
      })}

      {/* Error message */}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {/* Bottom bar */}
      <div className="fixed bottom-0 left-0 right-0 border-t bg-background px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => setPhase("select")}
          >
            Back to Sources
          </Button>
          <Button
            onClick={async () => {
              await saveFills();
              await handleGenerate();
            }}
            disabled={generating}
          >
            {generating ? "Exporting..." : "Export to Excel"}
          </Button>
        </div>
      </div>
    </div>
  );
}
