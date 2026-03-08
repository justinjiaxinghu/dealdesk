"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/interfaces/api";
import { UserMessage } from "./user-message";
import { AssistantMessage } from "./assistant-message";

interface ChatThreadProps {
  messages: ChatMessage[];
  loading?: boolean;
}

export function ChatThread({ messages, loading = false }: ChatThreadProps) {
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
          <AssistantMessage key={msg.id} message={msg} />
        )
      )}

      {loading && (
        <div className="flex justify-start">
          <div className="max-w-[85%] rounded-2xl rounded-bl-md bg-muted px-4 py-3">
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
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
