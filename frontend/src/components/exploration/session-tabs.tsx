"use client";

import { useState } from "react";
import type { ChatSession } from "@/interfaces/api";
import { Button } from "@/components/ui/button";

interface SessionTabsProps {
  sessions: ChatSession[];
  activeTabId: string | null;
  onSelectTab: (id: string | null) => void;
  onCloseTab: (id: string) => void;
  onNewTab: () => void;
}

export function SessionTabs({
  sessions,
  activeTabId,
  onSelectTab,
  onCloseTab,
  onNewTab,
}: SessionTabsProps) {
  const [historyOpen, setHistoryOpen] = useState(false);

  const activeSession = sessions.find((s) => s.id === activeTabId);
  const activeLabel = activeTabId === null
    ? "Overview"
    : activeSession?.title || "Untitled";

  return (
    <div className="flex items-center gap-2 border-b pb-2">
      {/* Current view selector */}
      <div className="relative">
        <button
          className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md border bg-background hover:bg-muted transition-colors"
          onClick={() => setHistoryOpen(!historyOpen)}
        >
          <span className="truncate max-w-[200px]">{activeLabel}</span>
          <svg
            className={`w-3.5 h-3.5 text-muted-foreground transition-transform ${historyOpen ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {/* Dropdown */}
        {historyOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-10"
              onClick={() => setHistoryOpen(false)}
            />
            <div className="absolute top-full left-0 mt-1 w-72 bg-background border rounded-lg shadow-lg z-20 py-1 max-h-80 overflow-y-auto">
              {/* Overview */}
              <button
                className={`w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors ${
                  activeTabId === null ? "bg-muted font-medium" : ""
                }`}
                onClick={() => {
                  onSelectTab(null);
                  setHistoryOpen(false);
                }}
              >
                Overview
              </button>

              {sessions.length > 0 && (
                <div className="border-t my-1" />
              )}

              {/* Chat sessions */}
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={`flex items-center justify-between px-3 py-2 text-sm hover:bg-muted transition-colors group ${
                    activeTabId === session.id ? "bg-muted font-medium" : ""
                  }`}
                >
                  <button
                    className="flex-1 text-left truncate"
                    onClick={() => {
                      onSelectTab(session.id);
                      setHistoryOpen(false);
                    }}
                  >
                    {session.title || "Untitled"}
                  </button>
                  <button
                    className="ml-2 p-0.5 rounded text-muted-foreground hover:text-foreground hover:bg-background opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation();
                      onCloseTab(session.id);
                    }}
                    title="Delete chat"
                  >
                    <svg
                      className="w-3.5 h-3.5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}

              {sessions.length === 0 && (
                <div className="px-3 py-2 text-sm text-muted-foreground">
                  No previous chats
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* New chat button */}
      <Button
        variant="ghost"
        size="sm"
        className="text-xs gap-1"
        onClick={onNewTab}
      >
        <svg
          className="w-3.5 h-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        New Chat
      </Button>
    </div>
  );
}
