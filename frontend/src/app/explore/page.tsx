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
  const { messages, setMessages, sending, sendMessage } = useChat(activeTabId);

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
        // Send message and fetch results for the new session directly
        // (don't rely on sendMessage from useChat which has stale sessionId)
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
    <div className="h-screen flex flex-col bg-background">
      <div className="max-w-7xl w-full mx-auto px-6 pt-8 pb-2 flex flex-col flex-1 min-h-0">
        {/* Header */}
        <div className="mb-4">
          <h1 className="text-2xl font-bold tracking-tight">
            Market Exploration
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Search for comparable properties and market data without a specific
            deal context.
          </p>
        </div>

        {/* Session tabs */}
        <SessionTabs
          sessions={sessions}
          activeTabId={activeTabId}
          onSelectTab={handleSelectTab}
          onCloseTab={handleCloseTab}
          onNewTab={handleNewTab}
        />

        {/* Active tab content */}
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

        {/* Chat input at bottom */}
        <SearchBar onSearch={handleSearch} loading={searchLoading || sending} />
      </div>
    </div>
  );
}
