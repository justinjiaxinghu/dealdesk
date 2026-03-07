"use client";

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
  return (
    <div className="flex items-center gap-1 border-b overflow-x-auto">
      {/* Overview tab (always first, not closeable) */}
      <button
        className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
          activeTabId === null
            ? "border-primary text-foreground"
            : "border-transparent text-muted-foreground hover:text-foreground"
        }`}
        onClick={() => onSelectTab(null)}
      >
        Overview
      </button>

      {/* Dynamic chat session tabs */}
      {sessions.map((session) => (
        <div
          key={session.id}
          className={`flex items-center gap-1 px-3 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
            activeTabId === session.id
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <button
            className="truncate max-w-[160px]"
            onClick={() => onSelectTab(session.id)}
            title={session.title}
          >
            {session.title || "Untitled"}
          </button>
          <button
            className="ml-1 rounded-sm p-0.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              onCloseTab(session.id);
            }}
            title="Close tab"
          >
            <svg
              className="w-3 h-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      ))}

      {/* New tab button */}
      <Button
        variant="ghost"
        size="icon-xs"
        className="ml-1 shrink-0"
        onClick={onNewTab}
        title="New chat"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 4v16m8-8H4"
          />
        </svg>
      </Button>
    </div>
  );
}
