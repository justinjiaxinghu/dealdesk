"use client";

import { useEffect, useRef, useState } from "react";
import type { ChatSession } from "@/interfaces/api";
import { Button } from "@/components/ui/button";

interface SessionTabsProps {
  sessions: ChatSession[];
  activeTabId: string | null;
  onSelectTab: (id: string | null) => void;
  onCloseTab: (id: string) => void;
  onNewTab: () => void;
  onRenameTab?: (id: string, newTitle: string) => void;
  saved?: boolean;
  onToggleSave?: () => void;
}

export function SessionTabs({
  sessions,
  activeTabId,
  onSelectTab,
  onCloseTab,
  onNewTab,
  onRenameTab,
  saved,
  onToggleSave,
}: SessionTabsProps) {
  const [historyOpen, setHistoryOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const editInputRef = useRef<HTMLInputElement>(null);

  const activeSession = sessions.find((s) => s.id === activeTabId);
  const activeLabel = activeSession?.title || "New Chat";

  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingId]);

  function startRename(session: ChatSession, e: React.MouseEvent) {
    e.stopPropagation();
    setEditingId(session.id);
    setEditValue(session.title || "");
  }

  function commitRename() {
    if (editingId && editValue.trim() && onRenameTab) {
      onRenameTab(editingId, editValue.trim());
    }
    setEditingId(null);
  }

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
              onClick={() => {
                setHistoryOpen(false);
                setEditingId(null);
              }}
            />
            <div className="absolute top-full left-0 mt-1 w-72 bg-background border rounded-lg shadow-lg z-20 py-1 max-h-80 overflow-y-auto">
              {/* Chat sessions */}
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={`flex items-center justify-between px-3 py-2 text-sm hover:bg-muted transition-colors group ${
                    activeTabId === session.id ? "bg-muted font-medium" : ""
                  }`}
                >
                  {editingId === session.id ? (
                    <input
                      ref={editInputRef}
                      className="flex-1 text-sm bg-transparent border-b border-foreground outline-none py-0"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          commitRename();
                          setHistoryOpen(false);
                        }
                        if (e.key === "Escape") setEditingId(null);
                      }}
                      onBlur={commitRename}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <button
                      className="flex-1 text-left truncate"
                      onClick={() => {
                        onSelectTab(session.id);
                        setHistoryOpen(false);
                      }}
                    >
                      {session.title || "Untitled"}
                    </button>
                  )}

                  <div className="flex items-center gap-0.5 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    {/* Rename button */}
                    {onRenameTab && editingId !== session.id && (
                      <button
                        className="p-0.5 rounded text-muted-foreground hover:text-foreground hover:bg-background"
                        onClick={(e) => startRename(session, e)}
                        title="Rename chat"
                      >
                        <svg
                          className="w-3.5 h-3.5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                    )}
                    {/* Delete button */}
                    <button
                      className="p-0.5 rounded text-muted-foreground hover:text-foreground hover:bg-background"
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
                </div>
              ))}

              {sessions.length === 0 && (
                <div className="px-3 py-2 text-sm text-muted-foreground">
                  No chats yet — type a message to start
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

      {/* Save exploration button */}
      {onToggleSave && (
        <Button
          variant="ghost"
          size="sm"
          className="text-xs gap-1 ml-auto"
          onClick={onToggleSave}
          title={saved ? "Unsave discovery" : "Save discovery"}
        >
          <svg
            className="w-3.5 h-3.5"
            fill={saved ? "currentColor" : "none"}
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
            />
          </svg>
          {saved ? "Saved" : "Save"}
        </Button>
      )}
    </div>
  );
}
