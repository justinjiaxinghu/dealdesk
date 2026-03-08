"use client";

import { use, useCallback, useEffect, useRef, useState } from "react";

import { DealSidebar } from "@/components/layout/deal-sidebar";
import { SearchBar } from "@/components/exploration/search-bar";
import { SessionTabs } from "@/components/exploration/session-tabs";
import { ChatThread } from "@/components/exploration/chat-thread";
import { OverviewTab } from "@/components/exploration/overview-tab";
import { useDeal } from "@/hooks/use-deal";
import { useExploration } from "@/hooks/use-exploration";
import { useChat } from "@/hooks/use-chat";
import { explorationService } from "@/services/exploration.service";
import { chatService } from "@/services/chat.service";
import { assumptionService } from "@/services/assumption.service";
import { compsService } from "@/services/comps.service";
import { documentService } from "@/services/document.service";
import { exportService } from "@/services/export.service";
import { historicalFinancialService } from "@/services/historical-financial.service";
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
    comps,
    historicalFinancials,
    loading,
    refresh,
  } = useDeal(id);

  // --- Exploration state ---
  const [explorationId, setExplorationId] = useState<string | null>(null);
  const [activeTabId, setActiveTabId] = useState<string | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const explorationInitRef = useRef(false);

  // --- Pipeline state ---
  const [pipelineStep, setPipelineStep] = useState<
    "extract" | "historical" | "assumptions" | "validate" | "comps" | null
  >(null);
  const [pipelineDetail, setPipelineDetail] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const pipelineRanRef = useRef(false);

  // --- Initialize exploration session on mount ---
  useEffect(() => {
    if (explorationInitRef.current) return;
    explorationInitRef.current = true;

    async function initExploration() {
      try {
        // Try to find existing explorations for this deal by listing all and filtering
        const allExplorations = await explorationService.list();
        const existing = allExplorations.find((e) => e.deal_id === id);
        if (existing) {
          setExplorationId(existing.id);
        } else {
          const newExploration = await explorationService.createForDeal(id);
          setExplorationId(newExploration.id);
        }
      } catch (err) {
        console.error("Failed to initialize exploration", err);
        // Try creating fresh if listing failed
        try {
          const newExploration = await explorationService.createForDeal(id);
          setExplorationId(newExploration.id);
        } catch {
          console.error("Failed to create exploration session");
        }
      }
    }

    initExploration();
  }, [id]);

  const { sessions, refresh: refreshExploration } =
    useExploration(explorationId);
  const { messages, sending, sendMessage, refresh: refreshMessages } =
    useChat(activeTabId);

  // --- Auto-pipeline: chain extraction polling -> benchmarks -> validation -> comps ---
  useEffect(() => {
    if (loading || !deal || pipelineRanRef.current) return;

    const allDocsComplete =
      documents.length > 0 &&
      documents.every((d) => d.processing_status === "complete");
    if (
      allDocsComplete &&
      historicalFinancials.length > 0 &&
      assumptions.length > 0 &&
      validations.length > 0 &&
      comps.length > 0
    )
      return;

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
              d.processing_status === "error"
          );
        }
        if (cancelled) return;
        await refresh();

        // Step 2: Extract historical financials from each completed doc
        const freshDocs = await documentService.list(id);
        const completedDocs = freshDocs.filter(
          (d) => d.processing_status === "complete"
        );
        const existingHf = await historicalFinancialService.list(id);
        if (existingHf.length === 0 && completedDocs.length > 0) {
          if (cancelled) return;
          setPipelineStep("historical");
          setPipelineDetail("Extracting historical financials from OM...");
          await Promise.allSettled(
            completedDocs.map((d) =>
              historicalFinancialService.extract(id, d.id)
            )
          );
          if (cancelled) return;
          await refresh();
        }

        // Step 3: Generate benchmarks if none exist yet
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

        // Step 4: Validate OM fields (two-phase: quick then deep)
        const freshValidations = await validationService.list(id);
        if (freshValidations.length === 0) {
          if (cancelled) return;
          setPipelineStep("validate");

          setPipelineDetail(
            "Phase 1: Quick search -- spot-checking key metrics..."
          );
          await validationService.validate(id, "quick");
          if (cancelled) return;
          await refresh();

          setPipelineDetail(
            "Phase 2: Deep search -- researching comps and market reports..."
          );
          await validationService.validate(id, "deep");
          if (cancelled) return;
          await refresh();
        }

        // Step 5: Find comparable properties
        const freshComps = await compsService.list(id);
        if (freshComps.length === 0) {
          if (cancelled) return;
          setPipelineStep("comps");
          setPipelineDetail("Searching for comparable properties...");
          await compsService.search(id);
          if (cancelled) return;
          await refresh();
        }
      } catch (err) {
        setActionError(
          err instanceof Error ? err.message : "Pipeline step failed"
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

  // --- Handlers ---

  const handleSearch = useCallback(
    async (query: string, connectors: string[]) => {
      if (!explorationId) return;
      setSearchLoading(true);
      try {
        // Create a new chat session for this search
        const session = await chatService.createSession(
          explorationId,
          query.slice(0, 60),
          connectors
        );
        await refreshExploration();
        setActiveTabId(session.id);

        // Send the message
        await chatService.sendMessage(session.id, query, connectors);
        // Refresh messages for the new active session
        await refreshMessages();
      } catch (err) {
        console.error("Search failed", err);
        setActionError(
          err instanceof Error ? err.message : "Search failed"
        );
      } finally {
        setSearchLoading(false);
      }
    },
    [explorationId, refreshExploration, refreshMessages]
  );

  const handleNewTab = useCallback(async () => {
    if (!explorationId) return;
    try {
      const session = await chatService.createSession(explorationId);
      await refreshExploration();
      setActiveTabId(session.id);
    } catch (err) {
      console.error("Failed to create new session", err);
    }
  }, [explorationId, refreshExploration]);

  const handleCloseTab = useCallback(
    async (sessionId: string) => {
      try {
        await chatService.deleteSession(sessionId);
        await refreshExploration();
        // If we closed the active tab, go back to overview
        if (activeTabId === sessionId) {
          setActiveTabId(null);
        }
      } catch (err) {
        console.error("Failed to close session", err);
      }
    },
    [activeTabId, refreshExploration]
  );

  const handleSelectTab = useCallback((tabId: string | null) => {
    setActiveTabId(tabId);
  }, []);

  function handleExport() {
    const activeSetId =
      assumptionSets.length > 0 ? assumptionSets[0].id : null;
    if (!activeSetId) return;
    exportService.downloadXlsx(activeSetId);
  }

  const handleSelectProperty = useCallback((_index: number) => {
    // Placeholder: could open a detail panel or navigate
  }, []);

  // --- Loading / error states ---
  if (loading) {
    return (
      <div className="text-muted-foreground py-12 px-6">Loading deal...</div>
    );
  }

  if (!deal) {
    return <div className="text-red-600 py-12 px-6">Deal not found.</div>;
  }

  return (
    <div className="flex h-[calc(100vh-64px)]">
      {/* Left pane: Sidebar */}
      <DealSidebar
        deal={deal}
        documents={documents}
        extractedFields={fields}
        validations={validations}
        assumptions={assumptions}
        historicalFinancials={historicalFinancials}
        loading={loading}
        onExport={handleExport}
      />

      {/* Right pane: Exploration */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Pipeline status banner */}
        {pipelineStep && (
          <div className="bg-blue-50 border-b border-blue-200 px-6 py-2 text-sm text-blue-800 flex items-center gap-2">
            <svg
              className="w-4 h-4 animate-spin shrink-0"
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
            <span className="font-medium capitalize">{pipelineStep}:</span>
            <span>{pipelineDetail}</span>
          </div>
        )}

        {actionError && (
          <div className="bg-red-50 border-b border-red-200 text-red-700 px-6 py-2 text-sm">
            {actionError}
          </div>
        )}

        {/* Search bar */}
        <div className="px-6 pt-4 pb-2">
          <SearchBar onSearch={handleSearch} loading={searchLoading} />
        </div>

        {/* Session tabs */}
        <div className="px-6">
          <SessionTabs
            sessions={sessions}
            activeTabId={activeTabId}
            onSelectTab={handleSelectTab}
            onCloseTab={handleCloseTab}
            onNewTab={handleNewTab}
          />
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {activeTabId === null ? (
            <OverviewTab
              deal={deal}
              properties={[]}
              onSelectProperty={handleSelectProperty}
            />
          ) : (
            <ChatThread messages={messages} loading={sending || searchLoading} />
          )}
        </div>
      </main>
    </div>
  );
}
