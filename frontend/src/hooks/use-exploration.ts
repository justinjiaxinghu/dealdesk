"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ExplorationSession, ChatSession } from "@/interfaces/api";
import { explorationService } from "@/services/exploration.service";
import { chatService } from "@/services/chat.service";

export function useExploration(explorationId: string | null) {
  const [exploration, setExploration] = useState<ExplorationSession | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const initialLoadDone = useRef(false);
  const prevExplorationId = useRef<string | null>(null);

  const refresh = useCallback(async () => {
    if (!explorationId) return;
    try {
      const [exp, sess] = await Promise.all([
        explorationService.get(explorationId),
        chatService.listSessions(explorationId),
      ]);
      setExploration(exp);
      setSessions(sess);
    } catch (err) {
      console.error("Failed to refresh exploration", err);
    } finally {
      if (!initialLoadDone.current) {
        initialLoadDone.current = true;
        setLoading(false);
      }
    }
  }, [explorationId]);

  // Reset sessions when exploration changes
  useEffect(() => {
    if (explorationId !== prevExplorationId.current) {
      prevExplorationId.current = explorationId;
      setSessions([]);
    }
    if (explorationId) refresh();
  }, [explorationId, refresh]);

  return { exploration, sessions, loading, refresh };
}
