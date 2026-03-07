"use client";

import { useCallback, useEffect, useState } from "react";
import type { ChatMessage } from "@/interfaces/api";
import { chatService } from "@/services/chat.service";

export function useChat(sessionId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  const loadMessages = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const msgs = await chatService.listMessages(sessionId);
      setMessages(msgs);
    } catch (err) {
      console.error("Failed to load messages", err);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (sessionId) loadMessages();
  }, [sessionId, loadMessages]);

  const sendMessage = useCallback(
    async (content: string, connectors: string[] = []) => {
      if (!sessionId) return;
      setSending(true);
      try {
        const newMessages = await chatService.sendMessage(sessionId, content, connectors);
        setMessages((prev) => [...prev, ...newMessages]);
      } catch (err) {
        console.error("Failed to send message", err);
      } finally {
        setSending(false);
      }
    },
    [sessionId]
  );

  return { messages, loading, sending, sendMessage, refresh: loadMessages };
}
