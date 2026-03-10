"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/interfaces/api";
import { UserMessage } from "./user-message";
import { AssistantMessage } from "./assistant-message";

interface ChatThreadProps {
  messages: ChatMessage[];
  loading?: boolean;
  dealId?: string | null;
  activeConnectors?: string[];
}

export function ChatThread({ messages, loading = false, dealId, activeConnectors = [] }: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages or loading state change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, loading]);

  // Filter out tool messages and empty assistant messages (tool-call intermediaries)
  const visibleMessages = messages.filter(
    (m) => m.role !== "tool" && !(m.role === "assistant" && (!m.content || m.content.trim() === ""))
  );

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
      {visibleMessages.length === 0 && !loading && (
        <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
          Start a conversation by searching above.
        </div>
      )}

      {visibleMessages.map((msg) =>
        msg.role === "user" ? (
          <UserMessage key={msg.id} message={msg} />
        ) : (
          <AssistantMessage key={msg.id} message={msg} dealId={dealId} />
        )
      )}

      {loading && (
        <div className="flex justify-start">
          <div className="max-w-[85%] rounded-2xl rounded-bl-md bg-muted px-4 py-3 space-y-2">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:300ms]" />
              </div>
              <span className="text-sm text-muted-foreground">
                Searching and analyzing...
              </span>
            </div>
            {activeConnectors.length > 0 && (
              <div className="flex items-center gap-1.5 flex-wrap">
                {activeConnectors.map((c) => (
                  <span
                    key={c}
                    className="inline-flex items-center gap-1 rounded-full bg-blue-100 dark:bg-blue-900/40 px-2 py-0.5 text-xs font-medium text-blue-700 dark:text-blue-300"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                    {c.replace("_", " ").replace(/\b\w/g, (l: string) => l.toUpperCase())}
                  </span>
                ))}
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 dark:bg-emerald-900/40 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Web Search
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
