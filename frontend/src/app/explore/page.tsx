"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
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

  const handleNewExploration = async () => {
    const exp = await explorationService.createFree("Market Discovery");
    router.push(`/explore?exploration=${exp.id}`);
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
        <Button onClick={handleNewExploration}>New Discovery</Button>
      </div>

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
                  router.push(
                    exp.deal_id
                      ? `/deals/${exp.deal_id}`
                      : `/explore?exploration=${exp.id}`
                  )
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

/** Wrapper that calls useDeal (which must be called unconditionally) and renders DealSidebar */
function DealSidebarConnected({ dealId }: { dealId: string }) {
  const {
    deal,
    documents,
    fields,
    assumptions,
    validations,
    historicalFinancials,
    loading,
  } = useDeal(dealId);

  return (
    <DealSidebar
      deal={deal}
      documents={documents}
      extractedFields={fields}
      validations={validations}
      assumptions={assumptions}
      historicalFinancials={historicalFinancials}
      loading={loading}
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
      } catch (err) {
        console.error("Search failed", err);
      } finally {
        setSearchLoading(false);
      }
    },
    [explorationId, refresh, setMessages]
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
          saved={exploration?.saved}
          onToggleSave={handleToggleSave}
        />

        <div className="flex-1 overflow-y-auto mt-2">
          {activeTabId === null ? (
            <OverviewTab
              deal={null}
              properties={[]}
              onSelectProperty={handleSelectProperty}
            />
          ) : (
            <ChatThread messages={messages} loading={sending || searchLoading} />
          )}
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
