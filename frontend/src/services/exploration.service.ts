import { apiFetch } from "./api-client";
import type { ExplorationSession } from "@/interfaces/api";

export const explorationService = {
  createForDeal: (dealId: string, name = "Untitled Exploration") =>
    apiFetch<ExplorationSession>(`/deals/${dealId}/explorations`, {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  createFree: (name = "Untitled Exploration") =>
    apiFetch<ExplorationSession>("/explorations", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  list: () => apiFetch<ExplorationSession[]>("/explorations"),

  listByDeal: (dealId: string) =>
    apiFetch<ExplorationSession[]>(`/deals/${dealId}/explorations`),

  get: (id: string) => apiFetch<ExplorationSession>(`/explorations/${id}`),

  update: (id: string, data: { name?: string; saved?: boolean }) =>
    apiFetch<ExplorationSession>(`/explorations/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    apiFetch<void>(`/explorations/${id}`, { method: "DELETE" }),
};
