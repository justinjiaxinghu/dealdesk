"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { SearchBar } from "@/components/exploration/search-bar";
import { SessionTabs } from "@/components/exploration/session-tabs";
import { OverviewTab } from "@/components/exploration/overview-tab";
import { ChatThread } from "@/components/exploration/chat-thread";
import { useExploration } from "@/hooks/use-exploration";
import { useChat } from "@/hooks/use-chat";
import { explorationService } from "@/services/exploration.service";
import { chatService } from "@/services/chat.service";

export default function ExplorePage() {
  const [explorationId, setExplorationId] = useState<string | null>(null);
  const [activeTabId, setActiveTabId] = useState<string | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const initRef = useRef(false);

  // Create a temporary exploration session on mount (no deal context)
  useEffect(() => {
    if (initRef.current) return;
    initRef.current = true;
    explorationService.createFree("Market Exploration").then((exp) => {
      setExplorationId(exp.id);
    });
  }, []);

  const { sessions, refresh } = useExploration(explorationId);
  const { messages, sending, sendMessage } = useChat(activeTabId);

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
        await sendMessage(query, connectors);
        await refresh();
      } catch (err) {
        console.error("Search failed", err);
      } finally {
        setSearchLoading(false);
      }
    },
    [explorationId, refresh, sendMessage]
  );

  // Tab management
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

  const handleSelectProperty = useCallback((_index: number) => {
    // Property detail interaction — placeholder for future drill-down
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Market Exploration
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Search for comparable properties and market data without a specific
            deal context.
          </p>
        </div>

        {/* Search bar */}
        <SearchBar onSearch={handleSearch} loading={searchLoading || sending} />

        {/* Session tabs */}
        <SessionTabs
          sessions={sessions}
          activeTabId={activeTabId}
          onSelectTab={handleSelectTab}
          onCloseTab={handleCloseTab}
          onNewTab={handleNewTab}
        />

        {/* Active tab content */}
        <div className="min-h-[400px]">
          {activeTabId === null ? (
            <OverviewTab
              deal={null}
              properties={[]}
              onSelectProperty={handleSelectProperty}
            />
          ) : (
            <ChatThread messages={messages} loading={sending} />
          )}
        </div>
      </div>
    </div>
  );
}
