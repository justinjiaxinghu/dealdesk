"use client";

import { use, useEffect, useRef, useState } from "react";

import { AssumptionEditor } from "@/components/assumptions/assumption-editor";
import { DealProgressBar } from "@/components/deals/deal-progress-bar";
import { ProcessingTracker } from "@/components/documents/processing-tracker";
import { ExtractedFieldsTable } from "@/components/extraction/extracted-fields-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDeal } from "@/hooks/use-deal";
import { ValidationTable } from "@/components/validation/validation-table";
import { assumptionService } from "@/services/assumption.service";
import { documentService } from "@/services/document.service";
import { exportService } from "@/services/export.service";
import { validationService } from "@/services/validation.service";

export default function DealWorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const {
    deal,
    documents,
    fields,
    assumptionSets,
    assumptions,
    validations,
    loading,
    refresh,
  } = useDeal(id);

  const [generatingBenchmarks, setGeneratingBenchmarks] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pipelineStep, setPipelineStep] = useState<
    "extract" | "assumptions" | "validate" | null
  >(null);
  const [pipelineDetail, setPipelineDetail] = useState<string | null>(null);
  const pipelineRanRef = useRef(false);

  // Auto-pipeline: chain extraction polling → benchmark generation.
  // Depends only on [loading] — fires once when initial data arrives.
  // The pipeline polls internally for documents/extraction/benchmarks,
  // so it handles the race condition where navigation happens before upload completes.
  useEffect(() => {
    if (loading || !deal || pipelineRanRef.current) return;

    // Everything already done — no pipeline needed
    const allDocsComplete =
      documents.length > 0 &&
      documents.every((d) => d.processing_status === "complete");
    if (allDocsComplete && assumptions.length > 0 && validations.length > 0) return;

    pipelineRanRef.current = true;
    let cancelled = false;

    async function runPipeline() {
      try {
        // Step 1: Wait for documents to appear + extraction to complete
        setPipelineStep("extract");
        setPipelineDetail("Waiting for document upload...");
        let extractionDone = false;
        while (!extractionDone && !cancelled) {
          await new Promise((r) => setTimeout(r, 2000));
          if (cancelled) return;
          const docs = await documentService.list(id);
          if (docs.length === 0) continue;
          setPipelineDetail("Extracting text and tables from PDF...");
          extractionDone = docs.every(
            (d) =>
              d.processing_status === "complete" ||
              d.processing_status === "error",
          );
        }
        if (cancelled) return;
        await refresh();

        // Step 2: Generate benchmarks if none exist yet
        const freshSets = await assumptionService.listSets(id);
        const freshSetId = freshSets.length > 0 ? freshSets[0].id : null;

        let freshAssumptions: typeof assumptions = [];
        if (freshSetId) {
          freshAssumptions =
            await assumptionService.listAssumptions(freshSetId);
        }

        if (freshAssumptions.length === 0) {
          if (cancelled) return;
          setPipelineStep("assumptions");
          setPipelineDetail("Generating AI market benchmarks...");
          await assumptionService.generateBenchmarks(id);
          if (cancelled) return;
          await refresh();
        }

        // Step 3: Validate OM fields (two-phase: quick then deep)
        const freshValidations = await validationService.list(id);
        if (freshValidations.length === 0) {
          if (cancelled) return;
          setPipelineStep("validate");

          // Phase 1: Quick search
          setPipelineDetail("Phase 1: Quick search — spot-checking key metrics...");
          await validationService.validate(id, "quick");
          if (cancelled) return;
          await refresh();

          // Phase 2: Deep search
          setPipelineDetail("Phase 2: Deep search — researching comps and market reports...");
          await validationService.validate(id, "deep");
          if (cancelled) return;
          await refresh();
        }
      } catch (err) {
        console.error("Auto-pipeline error:", err);
        setActionError(
          err instanceof Error ? err.message : "Pipeline step failed",
        );
      } finally {
        if (!cancelled) {
          setPipelineStep(null);
          setPipelineDetail(null);
        }
      }
    }

    runPipeline();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

  if (loading) {
    return <div className="text-muted-foreground py-12">Loading deal...</div>;
  }

  if (!deal) {
    return (
      <div className="text-red-600 py-12">Deal not found.</div>
    );
  }

  const activeSetId = assumptionSets.length > 0 ? assumptionSets[0].id : null;

  function handleExport() {
    if (!activeSetId) return;
    exportService.downloadXlsx(activeSetId);
  }

  async function handleGenerateBenchmarks() {
    setGeneratingBenchmarks(true);
    setActionError(null);
    try {
      await assumptionService.generateBenchmarks(id);
      await refresh();
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Failed to generate benchmarks",
      );
    } finally {
      setGeneratingBenchmarks(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{deal.name}</h1>
          <p className="text-muted-foreground">
            {deal.address}, {deal.city}, {deal.state}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline">{deal.property_type}</Badge>
            {deal.square_feet && (
              <span className="text-sm text-muted-foreground">
                {deal.square_feet.toLocaleString()} sq ft
              </span>
            )}
          </div>
        </div>
        <Button
          onClick={handleExport}
          disabled={!activeSetId}
        >
          Export XLSX
        </Button>
      </div>

      {actionError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
          {actionError}
        </div>
      )}

      {/* Progress Bar */}
      <DealProgressBar
        hasDocuments={documents.length > 0}
        hasFields={fields.length > 0}
        hasAssumptions={assumptions.length > 0}
        hasValidations={validations.length > 0}
        activeStep={pipelineStep}
        activeDetail={pipelineDetail}
      />

      {/* Tabbed Content */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="extraction">Extraction</TabsTrigger>
          <TabsTrigger value="assumptions">Assumptions</TabsTrigger>
          <TabsTrigger value="validation">Validation</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6 pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Deal Details</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                <div>
                  <dt className="text-muted-foreground">Name</dt>
                  <dd className="font-medium">{deal.name}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Property Type</dt>
                  <dd className="font-medium">{deal.property_type}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Address</dt>
                  <dd className="font-medium">
                    {deal.address}, {deal.city}, {deal.state}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Square Feet</dt>
                  <dd className="font-medium">
                    {deal.square_feet
                      ? deal.square_feet.toLocaleString()
                      : "-"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Created</dt>
                  <dd className="font-medium">
                    {new Date(deal.created_at).toLocaleString()}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Documents</CardTitle>
            </CardHeader>
            <CardContent>
              {documents.length === 0 ? (
                <p className="text-muted-foreground text-sm">
                  No documents uploaded yet.
                </p>
              ) : (
                <div className="space-y-4">
                  {documents.map((doc) => (
                    <ProcessingTracker key={doc.id} document={doc} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Extraction Tab */}
        <TabsContent value="extraction" className="pt-4">
          <ExtractedFieldsTable fields={fields} />
        </TabsContent>

        {/* Assumptions Tab */}
        <TabsContent value="assumptions" className="space-y-4 pt-4">
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={handleGenerateBenchmarks}
              disabled={generatingBenchmarks}
            >
              {generatingBenchmarks
                ? "Regenerating..."
                : assumptions.length > 0
                  ? "Regenerate AI Benchmarks"
                  : "Generate AI Benchmarks"}
            </Button>
          </div>

          <AssumptionEditor assumptions={assumptions} />
        </TabsContent>

        {/* Validation Tab */}
        <TabsContent value="validation" className="pt-4">
          <ValidationTable validations={validations} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
