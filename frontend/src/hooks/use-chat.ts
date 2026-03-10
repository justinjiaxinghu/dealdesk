"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage } from "@/interfaces/api";
import { chatService } from "@/services/chat.service";

export function useChat(sessionId: string | null) {
  const [messages, setMessagesInternal] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const skipNextLoad = useRef(false);

  // External setMessages that also skips the next auto-load
  const setMessages = useCallback((msgs: ChatMessage[]) => {
    skipNextLoad.current = true;
    setMessagesInternal(msgs);
  }, []);

  const loadMessages = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const msgs = await chatService.listMessages(sessionId);
      setMessagesInternal(msgs);
    } catch (err) {
      console.error("Failed to load messages", err);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) return;
    if (skipNextLoad.current) {
      skipNextLoad.current = false;
      return;
    }
    loadMessages();
  }, [sessionId, loadMessages]);

  const sendMessage = useCallback(
    async (content: string, connectors: string[] = []) => {
      if (!sessionId) return;
      setSending(true);
      try {
        const newMessages = await chatService.sendMessage(sessionId, content, connectors);
        setMessagesInternal((prev) => [...prev, ...newMessages]);
      } catch (err) {
        console.error("Failed to send message", err);
      } finally {
        setSending(false);
      }
    },
    [sessionId]
  );

  return { messages, setMessages, loading, sending, sendMessage, refresh: loadMessages };
}
