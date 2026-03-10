"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { reportService } from "@/services/report.service";
import type { ReportTemplate, ReportJob } from "@/interfaces/api";

export default function FillReportPage() {
  const params = useParams();
  const router = useRouter();
  const templateId = params.id as string;

  const [template, setTemplate] = useState<ReportTemplate | null>(null);
  const [job, setJob] = useState<ReportJob | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [fills, setFills] = useState<Record<string, { rows: string[][] }>>({});
  const [generating, setGenerating] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch template and create job on mount
  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        const tmpl = await reportService.getTemplate(templateId);
        if (cancelled) return;
        setTemplate(tmpl);

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

  const handleNext = useCallback(async () => {
    await saveFills();
    setCurrentIndex((i) => i + 1);
  }, [saveFills]);

  const handleBack = useCallback(() => {
    setCurrentIndex((i) => Math.max(0, i - 1));
  }, []);

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

  if (!template || !job) {
    return (
      <div className="text-muted-foreground py-12 text-center">
        Loading template...
      </div>
    );
  }

  const regions = template.regions;
  const totalSteps = regions.length;

  // Completed state
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

  // No regions edge case
  if (totalSteps === 0) {
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

  const region = regions[currentIndex];
  const regionFills = fills[region.region_id];
  const isLast = currentIndex === totalSteps - 1;
  const progressPercent = ((currentIndex + 1) / totalSteps) * 100;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">{template.name}</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Step {currentIndex + 1} of {totalSteps}
        </p>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-muted rounded-full h-2">
        <div
          className="bg-primary h-2 rounded-full transition-all duration-300"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Region info */}
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">{region.label}</h2>
        <p className="text-sm text-muted-foreground">
          {region.sheet_or_slide} &middot; {region.region_type}
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

      {/* Error message */}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {/* Navigation */}
      <div className="flex items-center justify-between pt-4">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={currentIndex === 0}
        >
          Back
        </Button>

        {isLast ? (
          <Button onClick={handleGenerate} disabled={generating}>
            {generating ? "Generating..." : "Generate Report"}
          </Button>
        ) : (
          <Button onClick={handleNext}>Next</Button>
        )}
      </div>
    </div>
  );
}
