import { apiFetch } from "./api-client";
import type { ChatSession, ChatMessage } from "@/interfaces/api";

export const chatService = {
  createSession: (explorationId: string, title = "New Search", connectors: string[] = []) =>
    apiFetch<ChatSession>(`/explorations/${explorationId}/sessions`, {
      method: "POST",
      body: JSON.stringify({ title, connectors }),
    }),

  listSessions: (explorationId: string) =>
    apiFetch<ChatSession[]>(`/explorations/${explorationId}/sessions`),

  getSession: (sessionId: string) =>
    apiFetch<ChatSession>(`/chat/sessions/${sessionId}`),

  updateSession: (sessionId: string, data: { title?: string }) =>
    apiFetch<ChatSession>(`/chat/sessions/${sessionId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteSession: (sessionId: string) =>
    apiFetch<void>(`/chat/sessions/${sessionId}`, { method: "DELETE" }),

  listMessages: (sessionId: string) =>
    apiFetch<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`),

  sendMessage: (sessionId: string, content: string, connectors: string[] = []) =>
    apiFetch<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, connectors }),
    }),
};
