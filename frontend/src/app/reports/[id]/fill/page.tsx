"use client";

// Requires: npm install xlsx
import * as XLSX from "xlsx";
import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { reportService } from "@/services/report.service";
import { connectorService } from "@/services/connector.service";
import type { ReportTemplate, ReportJob, Connector } from "@/interfaces/api";

type Phase = "select" | "preview";

export default function FillReportPage() {
  const params = useParams();
  const router = useRouter();
  const templateId = params.id as string;

  const [template, setTemplate] = useState<ReportTemplate | null>(null);
  const [job, setJob] = useState<ReportJob | null>(null);
  const [fills, setFills] = useState<Record<string, { rows: string[][] }>>({});
  const [error, setError] = useState<string | null>(null);

  // Phase 1 state
  const [phase, setPhase] = useState<Phase>("select");
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [selectedConnectors, setSelectedConnectors] = useState<Set<string>>(
    new Set(),
  );
  const [prompt, setPrompt] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  // Phase 2 (preview) state
  const [sheetData, setSheetData] = useState<Record<string, string[][]>>({});
  const [activeSheet, setActiveSheet] = useState<string>("");

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
      // 1. Run AI fill
      const updated = await reportService.aiFill(
        job.id,
        Array.from(selectedConnectors),
        prompt || undefined,
      );
      setJob(updated);

      // 2. Save fills to the job
      if (updated.fills) {
        await reportService.updateFills(job.id, updated.fills);
      }

      // 3. Generate the filled XLSX
      const generated = await reportService.generate(updated.id);
      setJob(generated);

      // 4. Fetch and parse the generated XLSX
      const resp = await fetch(reportService.downloadUrl(generated.id));
      const buffer = await resp.arrayBuffer();
      const wb = XLSX.read(buffer, { type: "array" });
      const data: Record<string, string[][]> = {};
      for (const name of wb.SheetNames) {
        data[name] = XLSX.utils.sheet_to_json(wb.Sheets[name], {
          header: 1,
        }) as string[][];
      }
      setSheetData(data);
      setActiveSheet(wb.SheetNames[0] ?? "");
      setPhase("preview");
    } catch (err) {
      console.error("AI fill failed", err);
      setError("AI fill failed. Please try again.");
    } finally {
      setAiLoading(false);
    }
  }, [job, selectedConnectors, prompt]);

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

  // --- Phase 2: Excel Preview ---
  const sheetNames = Object.keys(sheetData);
  const activeRows = sheetData[activeSheet] ?? [];

  // Determine the max number of columns across all rows in the active sheet
  const maxCols = activeRows.reduce(
    (max, row) => Math.max(max, row.length),
    0,
  );

  return (
    <div className="max-w-6xl mx-auto space-y-4 pb-24">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">{template.name}</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Preview of the generated report.
        </p>
      </div>

      {/* Sheet tabs */}
      {sheetNames.length > 1 && (
        <div className="flex items-center gap-0 border-b">
          {sheetNames.map((name) => (
            <button
              key={name}
              type="button"
              onClick={() => setActiveSheet(name)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                name === activeSheet
                  ? "border-foreground text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground"
              }`}
            >
              {name}
            </button>
          ))}
        </div>
      )}

      {/* Excel-like table */}
      <div className="border rounded-md overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          {activeRows.length > 0 && (
            <>
              {/* Header row */}
              <thead>
                <tr className="bg-gray-100 dark:bg-gray-800">
                  {Array.from({ length: maxCols }, (_, colIdx) => {
                    const cellValue = activeRows[0]?.[colIdx];
                    return (
                      <th
                        key={colIdx}
                        className="px-3 py-2 text-left font-bold text-sm text-foreground border border-gray-200 dark:border-gray-700 whitespace-nowrap"
                      >
                        {cellValue != null && cellValue !== ""
                          ? String(cellValue)
                          : ""}
                      </th>
                    );
                  })}
                </tr>
              </thead>

              {/* Data rows */}
              <tbody>
                {activeRows.slice(1).map((row, rowIdx) => (
                  <tr
                    key={rowIdx}
                    className={
                      rowIdx % 2 === 0
                        ? "bg-white dark:bg-gray-900"
                        : "bg-gray-50 dark:bg-gray-850"
                    }
                  >
                    {Array.from({ length: maxCols }, (_, colIdx) => {
                      const cellValue = row[colIdx];
                      return (
                        <td
                          key={colIdx}
                          className="px-3 py-1.5 text-sm text-foreground border border-gray-200 dark:border-gray-700 whitespace-nowrap"
                        >
                          {cellValue != null && cellValue !== ""
                            ? String(cellValue)
                            : ""}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </>
          )}

          {activeRows.length === 0 && (
            <tbody>
              <tr>
                <td className="px-3 py-8 text-center text-muted-foreground">
                  This sheet is empty.
                </td>
              </tr>
            </tbody>
          )}
        </table>
      </div>

      {/* Error message */}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {/* Bottom bar */}
      <div className="fixed bottom-0 left-0 right-0 border-t bg-background px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Button variant="outline" onClick={() => setPhase("select")}>
            Back to Sources
          </Button>
          <a
            href={reportService.downloadUrl(job.id)}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90"
          >
            Download Excel
          </a>
        </div>
      </div>
    </div>
  );
}
