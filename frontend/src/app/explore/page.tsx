"use client";

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FilterChip } from "@/components/ui/filter-chip";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SearchBar } from "@/components/exploration/search-bar";
import { SessionTabs } from "@/components/exploration/session-tabs";
import { OverviewTab } from "@/components/exploration/overview-tab";
import { ChatThread } from "@/components/exploration/chat-thread";
import { useExploration } from "@/hooks/use-exploration";
import { useChat } from "@/hooks/use-chat";
import { useDeal } from "@/hooks/use-deal";
import { DealSidebar } from "@/components/layout/deal-sidebar";
import type { ChatMessage, ExplorationSession } from "@/interfaces/api";
import { explorationService } from "@/services/exploration.service";
import { chatService } from "@/services/chat.service";
import { connectorService } from "@/services/connector.service";
import { assumptionService } from "@/services/assumption.service";
import { compsService } from "@/services/comps.service";
import { documentService } from "@/services/document.service";
import { historicalFinancialService } from "@/services/historical-financial.service";
import { validationService } from "@/services/validation.service";

function SavedExplorationsView() {
  const router = useRouter();
  const [explorations, setExplorations] = useState<ExplorationSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [nameFilter, setNameFilter] = useState("");
  const [contextFilter, setContextFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");

  useEffect(() => {
    explorationService
      .list()
      .then(setExplorations)
      .catch((err) => console.error("Failed to load explorations", err))
      .finally(() => setLoading(false));
  }, []);

  const nameOptions = useMemo(
    () => [...new Set(explorations.map((e) => e.name))].sort(),
    [explorations]
  );
  const contextOptions = useMemo(() => ["Free", "Deal-linked"], []);
  const tagOptions = useMemo(
    () => [...new Set(explorations.flatMap((e) => e.tags ?? []))].sort(),
    [explorations]
  );

  const filtered = useMemo(() => {
    return explorations.filter((exp) => {
      if (nameFilter && exp.name !== nameFilter) return false;
      if (contextFilter === "Free" && exp.deal_id) return false;
      if (contextFilter === "Deal-linked" && !exp.deal_id) return false;
      if (tagFilter && !(exp.tags ?? []).includes(tagFilter)) return false;
      return true;
    });
  }, [explorations, nameFilter, contextFilter, tagFilter]);

  const hasFilters = nameFilter || contextFilter || tagFilter;

  const [showNewDialog, setShowNewDialog] = useState(false);
  const [newName, setNewName] = useState("Market Discovery");
  const [creating, setCreating] = useState(false);

  const handleCreateExploration = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const exp = await explorationService.createFree(newName.trim());
      setShowNewDialog(false);
      setNewName("Market Discovery");
      router.push(`/explore?exploration=${exp.id}`);
    } catch (err) {
      console.error("Failed to create discovery", err);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Discovery</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Search for comparable properties and market data without a specific deal context.
          </p>
        </div>
        <Button onClick={() => setShowNewDialog(true)}>New Discovery</Button>
      </div>

      <Dialog open={showNewDialog} onOpenChange={setShowNewDialog}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>New Discovery</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="discovery-name">Name</Label>
            <Input
              id="discovery-name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="e.g. NYC Multifamily Research"
              className="mt-2"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter") handleCreateExploration();
              }}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateExploration} disabled={!newName.trim() || creating}>
              {creating ? "Creating..." : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="flex items-center gap-2 flex-wrap">
        <FilterChip
          label="Name"
          value={nameFilter}
          options={nameOptions}
          onChange={setNameFilter}
        />
        <FilterChip
          label="Context"
          value={contextFilter}
          options={contextOptions}
          onChange={setContextFilter}
        />
        <FilterChip
          label="Tag"
          value={tagFilter}
          options={tagOptions}
          onChange={setTagFilter}
        />
        {hasFilters && (
          <button
            onClick={() => {
              setNameFilter("");
              setContextFilter("");
              setTagFilter("");
            }}
            className="text-sm text-muted-foreground hover:text-foreground ml-1 cursor-pointer"
          >
            Clear all
          </button>
        )}
      </div>

      {loading ? (
        <div className="text-muted-foreground">Loading discoveries...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground mb-4">
            {explorations.length === 0
              ? "No saved discoveries yet."
              : "No discoveries match your filters."}
          </p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Context</TableHead>
              <TableHead>Tags</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((exp) => (
              <TableRow
                key={exp.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() =>
                  router.push(`/explore?exploration=${exp.id}`)
                }
              >
                <TableCell className="font-medium">{exp.name}</TableCell>
                <TableCell>
                  {exp.deal_id ? "Deal-linked" : "Free"}
                </TableCell>
                <TableCell>
                  <div className="flex gap-1 flex-wrap">
                    {(exp.tags ?? []).map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </TableCell>
                <TableCell>
                  {new Date(exp.created_at).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}

/** Wrapper that calls useDeal, runs the auto-pipeline, and renders DealSidebar */
function DealSidebarConnected({ dealId }: { dealId: string }) {
  const {
    deal,
    documents,
    fields,
    assumptions,
    validations,
    comps,
    historicalFinancials,
    loading,
    refresh,
  } = useDeal(dealId);

  const [pipelineStep, setPipelineStep] = useState<string | null>(null);
  const [pipelineDetail, setPipelineDetail] = useState<string | null>(null);
  const pipelineRanRef = useRef(false);

  useEffect(() => {
    if (loading || !deal || pipelineRanRef.current) return;
    if (documents.length === 0) return;

    // Check if any document is still processing (not yet complete)
    const hasProcessingDoc = documents.some(
      (d) => d.processing_status === "processing" || d.processing_status === "pending"
    );
    // If all docs are complete and we already have pipeline output, skip entirely
    const allDocsComplete = documents.every(
      (d) => d.processing_status === "complete" || d.processing_status === "error"
    );
    if (allDocsComplete && !hasProcessingDoc) {
      // Pipeline already ran if we have any extracted fields, assumptions, or validations
      if (fields.length > 0 || assumptions.length > 0 || validations.length > 0) {
        pipelineRanRef.current = true;
        return;
      }
    }

    pipelineRanRef.current = true;
    let cancelled = false;

    async function runPipeline() {
      try {
        // Step 1: Wait for extraction to complete (only if docs are still processing)
        if (!allDocsComplete) {
          setPipelineStep("extract");
          setPipelineDetail("Extracting text and tables from PDF...");
          let extractionDone = false;
          while (!extractionDone && !cancelled) {
            await new Promise((r) => setTimeout(r, 2000));
            if (cancelled) return;
            const docs = await documentService.list(dealId);
            if (docs.length === 0) continue;
            extractionDone = docs.every(
              (d) => d.processing_status === "complete" || d.processing_status === "error"
            );
          }
          if (cancelled) return;
          await refresh();
        }

        // Step 2: Extract historical financials (only if none exist)
        const freshDocs = await documentService.list(dealId);
        const completedDocs = freshDocs.filter((d) => d.processing_status === "complete");
        const existingHf = await historicalFinancialService.list(dealId);
        if (existingHf.length === 0 && completedDocs.length > 0) {
          if (cancelled) return;
          setPipelineStep("historical");
          setPipelineDetail("Extracting historical financials from OM...");
          await Promise.allSettled(
            completedDocs.map((d) => historicalFinancialService.extract(dealId, d.id))
          );
          if (cancelled) return;
          await refresh();
        }

        // Step 3: Generate benchmarks (only if none exist)
        const freshSets = await assumptionService.listSets(dealId);
        const freshSetId = freshSets.length > 0 ? freshSets[0].id : null;
        let freshAssumptions: typeof assumptions = [];
        if (freshSetId) {
          freshAssumptions = await assumptionService.listAssumptions(freshSetId);
        }
        if (freshAssumptions.length === 0) {
          if (cancelled) return;
          setPipelineStep("assumptions");
          setPipelineDetail("Generating AI market benchmarks...");
          await assumptionService.generateBenchmarks(dealId);
          if (cancelled) return;
          await refresh();
        }

        // Step 4: Validate OM fields (only if none exist)
        const freshValidations = await validationService.list(dealId);
        if (freshValidations.length === 0) {
          if (cancelled) return;
          setPipelineStep("validate");
          setPipelineDetail("Phase 1: Quick search...");
          await validationService.validate(dealId, "quick");
          if (cancelled) return;
          await refresh();
          setPipelineDetail("Phase 2: Deep search...");
          await validationService.validate(dealId, "deep");
          if (cancelled) return;
          await refresh();
        }

        // Step 5: Find comparable properties (only if none exist)
        const freshComps = await compsService.list(dealId);
        if (freshComps.length === 0) {
          if (cancelled) return;
          setPipelineStep("comps");
          setPipelineDetail("Searching for comparable properties...");
          await compsService.search(dealId);
          if (cancelled) return;
          await refresh();
        }
      } catch (err) {
        console.error("Pipeline error", err);
      } finally {
        if (!cancelled) {
          setPipelineStep(null);
          setPipelineDetail(null);
        }
      }
    }

    runPipeline();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

  return (
    <DealSidebar
      deal={deal}
      documents={documents}
      extractedFields={fields}
      validations={validations}
      assumptions={assumptions}
      historicalFinancials={historicalFinancials}
      loading={loading}
      pipelineStep={pipelineStep}
      pipelineDetail={pipelineDetail}
    />
  );
}

function ExploreWorkspace({ explorationId }: { explorationId: string }) {
  const [activeTabId, setActiveTabId] = useState<string | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [dealId, setDealId] = useState<string | null>(null);
  const [connectedSources, setConnectedSources] = useState<string[]>([]);

  useEffect(() => {
    connectorService.list().then((connectors) => {
      setConnectedSources(
        connectors.filter((c) => c.status === "connected").map((c) => c.provider)
      );
    });
  }, []);

  const { exploration, sessions, refresh } = useExploration(explorationId);
  const { messages, setMessages, sending } = useChat(activeTabId);

  // When exploration loads and has a deal_id, set it
  useEffect(() => {
    if (exploration?.deal_id) {
      setDealId(exploration.deal_id);
    }
  }, [exploration?.deal_id]);

  // Deal data is fetched via the DealSidebarConnected component below

  // Auto-select the latest chat session when sessions load
  useEffect(() => {
    if (sessions.length === 0) {
      if (activeTabId !== null) setActiveTabId(null);
      return;
    }
    if (activeTabId && !sessions.some((s) => s.id === activeTabId)) {
      setActiveTabId(sessions[sessions.length - 1].id);
      return;
    }
    if (!activeTabId) {
      setActiveTabId(sessions[sessions.length - 1].id);
    }
  }, [sessions, activeTabId]);

  const handleSearch = useCallback(
    async (query: string, connectors: string[]) => {
      setSearchLoading(true);
      try {
        // If there's already an active chat session, continue the conversation
        const sessionId = activeTabId;
        if (sessionId) {
          const optimisticUserMsg: ChatMessage = {
            id: "temp-" + Date.now(),
            session_id: sessionId,
            role: "user",
            content: query,
            tool_calls: null,
            created_at: new Date().toISOString(),
          };
          setMessages([...messages, optimisticUserMsg]);

          await chatService.sendMessage(sessionId, query, connectors);
          const msgs = await chatService.listMessages(sessionId);
          setMessages(msgs);
        } else {
          // No active session — create a new one
          const session = await chatService.createSession(
            explorationId,
            query.slice(0, 60),
            connectors
          );
          await refresh();
          setActiveTabId(session.id);

          const optimisticUserMsg: ChatMessage = {
            id: "temp-" + Date.now(),
            session_id: session.id,
            role: "user",
            content: query,
            tool_calls: null,
            created_at: new Date().toISOString(),
          };
          setMessages([optimisticUserMsg]);

          await chatService.sendMessage(session.id, query, connectors);
          const msgs = await chatService.listMessages(session.id);
          setMessages(msgs);
        }
      } catch (err) {
        console.error("Search failed", err);
      } finally {
        setSearchLoading(false);
      }
    },
    [explorationId, activeTabId, messages, refresh, setMessages]
  );

  const handleNewTab = useCallback(async () => {
    const session = await chatService.createSession(explorationId, "New Search");
    await refresh();
    setActiveTabId(session.id);
  }, [explorationId, refresh]);

  const handleCloseTab = useCallback(
    async (sessionId: string) => {
      await chatService.deleteSession(sessionId);
      if (activeTabId === sessionId) {
        setActiveTabId(null);
      }
      await refresh();
    },
    [activeTabId, refresh]
  );

  const handleSelectTab = useCallback((id: string | null) => {
    setActiveTabId(id);
  }, []);

  const handleRenameTab = useCallback(
    async (sessionId: string, newTitle: string) => {
      try {
        await chatService.updateSession(sessionId, { title: newTitle });
        await refresh();
      } catch (err) {
        console.error("Failed to rename chat", err);
      }
    },
    [refresh]
  );

  const handleSelectProperty = useCallback((_index: number) => {}, []);

  const handleToggleSave = useCallback(async () => {
    if (!exploration) return;
    try {
      await explorationService.update(explorationId, { saved: !exploration.saved });
      await refresh();
    } catch (err) {
      console.error("Failed to toggle save", err);
    }
  }, [explorationId, exploration, refresh]);

  const handleUploadOM = useCallback(async (file: File) => {
    try {
      const result = await explorationService.uploadOM(explorationId, file);
      setDealId(result.deal_id);
      await refresh();
    } catch (err) {
      console.error("OM upload failed", err);
    }
  }, [explorationId, refresh]);

  return (
    <div className="h-[calc(100vh-120px)] flex">
      {/* Deal sidebar — only visible when OM uploaded */}
      {dealId && (
        <div className="shrink-0 overflow-y-auto">
          <DealSidebarConnected dealId={dealId} />
        </div>
      )}

      {/* Main exploration pane */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="mb-4 px-4 pt-2">
          <h1 className="text-2xl font-bold tracking-tight">
            {exploration?.name ?? "Market Discovery"}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Search for comparable properties and market data.
          </p>
        </div>

        <SessionTabs
          sessions={sessions}
          activeTabId={activeTabId}
          onSelectTab={handleSelectTab}
          onCloseTab={handleCloseTab}
          onNewTab={handleNewTab}
          onRenameTab={handleRenameTab}
          saved={exploration?.saved}
          onToggleSave={handleToggleSave}
        />

        <div className="flex-1 overflow-y-auto mt-2">
          <ChatThread messages={messages} loading={sending || searchLoading} activeConnectors={connectedSources} />
        </div>

        <SearchBar onSearch={handleSearch} onUploadOM={handleUploadOM} loading={searchLoading || sending} connectedSources={connectedSources} />
      </div>
    </div>
  );
}

function ExploreContent() {
  const searchParams = useSearchParams();
  const requestedExplorationId = searchParams.get("exploration");

  if (requestedExplorationId) {
    return <ExploreWorkspace explorationId={requestedExplorationId} />;
  }

  return <SavedExplorationsView />;
}

export default function ExplorePage() {
  return (
    <Suspense>
      <ExploreContent />
    </Suspense>
  );
}
