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

  const visibleMessages = messages.filter((m) => m.role !== "tool");

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
          <div className="rounded-2xl rounded-bl-md bg-muted px-4 py-2.5">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:0ms]" />
              <span className="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:150ms]" />
              <span className="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:300ms]" />
              <span className="ml-2 text-sm text-muted-foreground">
                Thinking...
              </span>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
