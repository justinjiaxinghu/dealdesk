"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { SearchBar } from "@/components/exploration/search-bar";
import { SessionTabs } from "@/components/exploration/session-tabs";
import { OverviewTab } from "@/components/exploration/overview-tab";
import { ChatThread } from "@/components/exploration/chat-thread";
import { useExploration } from "@/hooks/use-exploration";
import { useChat } from "@/hooks/use-chat";
import type { ChatMessage } from "@/interfaces/api";
import { explorationService } from "@/services/exploration.service";
import { chatService } from "@/services/chat.service";

function ExploreContent() {
  const searchParams = useSearchParams();
  const requestedExplorationId = searchParams.get("exploration");

  const [explorationId, setExplorationId] = useState<string | null>(null);
  const [activeTabId, setActiveTabId] = useState<string | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);

  // Create a fresh exploration on mount, or load a saved one from query param.
  // Runs once per mount (component remounts on each navigation thanks to the key prop).
  useEffect(() => {
    let cancelled = false;
    async function initExploration() {
      if (requestedExplorationId) {
        setExplorationId(requestedExplorationId);
        return;
      }
      const exp = await explorationService.createFree("Market Exploration");
      if (!cancelled) setExplorationId(exp.id);
    }
    initExploration();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const { exploration, sessions, refresh } = useExploration(explorationId);
  const { messages, setMessages, sending, sendMessage } = useChat(activeTabId);

  // Auto-select the latest chat session when sessions load, and
  // ensure activeTabId always belongs to the current exploration's sessions
  useEffect(() => {
    if (sessions.length === 0) {
      if (activeTabId !== null) setActiveTabId(null);
      return;
    }
    // If current tab doesn't belong to this exploration's sessions, fix it
    if (activeTabId && !sessions.some((s) => s.id === activeTabId)) {
      setActiveTabId(sessions[sessions.length - 1].id);
      return;
    }
    // If no tab selected yet, pick the latest
    if (!activeTabId) {
      setActiveTabId(sessions[sessions.length - 1].id);
    }
  }, [sessions, activeTabId]);

  // Search creates a new session, sends the message, and switches to it
  const handleSearch = useCallback(
    async (query: string, connectors: string[]) => {
      if (!explorationId) return;
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
    if (!explorationId) return;
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
    if (!explorationId || !exploration) return;
    try {
      await explorationService.update(explorationId, { saved: !exploration.saved });
      await refresh();
    } catch (err) {
      console.error("Failed to toggle save", err);
    }
  }, [explorationId, exploration, refresh]);

  return (
    <div className="h-screen flex flex-col bg-background">
      <div className="max-w-7xl w-full mx-auto px-6 pt-8 pb-2 flex flex-col flex-1 min-h-0">
        <div className="mb-4">
          <h1 className="text-2xl font-bold tracking-tight">
            Market Exploration
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Search for comparable properties and market data without a specific
            deal context.
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

        <SearchBar onSearch={handleSearch} loading={searchLoading || sending} />
      </div>
    </div>
  );
}

export default function ExplorePage() {
  return (
    <Suspense>
      <ExploreContent />
    </Suspense>
  );
}
