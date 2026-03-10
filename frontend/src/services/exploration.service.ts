import { apiFetch, apiUpload } from "./api-client";
import type { ExplorationSession } from "@/interfaces/api";

export const explorationService = {
  createForDeal: (dealId: string, name = "Untitled Discovery") =>
    apiFetch<ExplorationSession>(`/deals/${dealId}/explorations`, {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  createFree: (name = "Untitled Discovery") =>
    apiFetch<ExplorationSession>("/explorations", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  list: () => apiFetch<ExplorationSession[]>("/explorations"),

  listFree: () => apiFetch<ExplorationSession[]>("/explorations/free"),

  listByDeal: (dealId: string) =>
    apiFetch<ExplorationSession[]>(`/deals/${dealId}/explorations`),

  get: (id: string) => apiFetch<ExplorationSession>(`/explorations/${id}`),

  update: (id: string, data: { name?: string; saved?: boolean; tags?: string[] }) =>
    apiFetch<ExplorationSession>(`/explorations/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    apiFetch<void>(`/explorations/${id}`, { method: "DELETE" }),

  async uploadOM(explorationId: string, file: File): Promise<{ deal_id: string; document_id: string; exploration_id: string }> {
    const formData = new FormData();
    formData.append("file", file);
    return apiUpload(`/explorations/${explorationId}/upload-om`, formData);
  },
};
