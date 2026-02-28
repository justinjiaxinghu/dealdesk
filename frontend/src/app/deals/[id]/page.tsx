"use client";

import { use, useState } from "react";

import { AssumptionEditor } from "@/components/assumptions/assumption-editor";
import { DealProgressBar } from "@/components/deals/deal-progress-bar";
import { ProcessingTracker } from "@/components/documents/processing-tracker";
import { ExtractedFieldsTable } from "@/components/extraction/extracted-fields-table";
import { ModelOutputs } from "@/components/model/model-outputs";
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
import { assumptionService } from "@/services/assumption.service";
import { exportService } from "@/services/export.service";
import { modelService } from "@/services/model.service";

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
    tables,
    assumptionSets,
    assumptions,
    modelResult,
    loading,
    refresh,
  } = useDeal(id);

  const [computing, setComputing] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [generatingBenchmarks, setGeneratingBenchmarks] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  if (loading) {
    return <div className="text-muted-foreground py-12">Loading deal...</div>;
  }

  if (!deal) {
    return (
      <div className="text-red-600 py-12">Deal not found.</div>
    );
  }

  const activeSetId = assumptionSets.length > 0 ? assumptionSets[0].id : null;

  async function handleCompute() {
    if (!activeSetId) return;
    setComputing(true);
    setActionError(null);
    try {
      await modelService.compute(activeSetId);
      await refresh();
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Failed to compute model",
      );
    } finally {
      setComputing(false);
    }
  }

  async function handleExport() {
    if (!activeSetId) return;
    setExporting(true);
    setActionError(null);
    try {
      await exportService.exportXlsx(activeSetId);
      await refresh();
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Failed to export",
      );
    } finally {
      setExporting(false);
    }
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
        <div className="flex gap-2">
          <Button
            onClick={handleCompute}
            disabled={computing || !activeSetId}
            variant="outline"
          >
            {computing ? "Computing..." : "Compute Model"}
          </Button>
          <Button
            onClick={handleExport}
            disabled={exporting || !activeSetId}
          >
            {exporting ? "Exporting..." : "Export XLSX"}
          </Button>
        </div>
      </div>

      {actionError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
          {actionError}
        </div>
      )}

      {/* Progress Bar */}
      <DealProgressBar
        status={deal.status}
        hasDocuments={documents.length > 0}
        hasFields={fields.length > 0}
        hasAssumptions={assumptions.length > 0}
        hasModelResult={modelResult !== null}
      />

      {/* Tabbed Content */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="extraction">Extraction</TabsTrigger>
          <TabsTrigger value="assumptions">Assumptions</TabsTrigger>
          <TabsTrigger value="model">Model</TabsTrigger>
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
                  <dt className="text-muted-foreground">Status</dt>
                  <dd className="font-medium">{deal.status}</dd>
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
          <ExtractedFieldsTable fields={fields} tables={tables} />
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
                ? "Generating..."
                : "Generate AI Benchmarks"}
            </Button>
          </div>

          {activeSetId ? (
            <AssumptionEditor
              setId={activeSetId}
              assumptions={assumptions}
              onSaved={refresh}
            />
          ) : (
            <p className="text-muted-foreground text-sm">
              No assumption set found. Process a document first to create
              an assumption set.
            </p>
          )}
        </TabsContent>

        {/* Model Tab */}
        <TabsContent value="model" className="pt-4">
          <ModelOutputs result={modelResult} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
