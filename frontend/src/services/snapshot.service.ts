import { apiFetch } from "./api-client";
import type { Snapshot, ExplorationSession } from "@/interfaces/api";

export const snapshotService = {
  create: (explorationId: string, name: string) =>
    apiFetch<Snapshot>(`/explorations/${explorationId}/snapshots`, {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  list: () => apiFetch<Snapshot[]>("/snapshots"),

  listForDeal: (dealId: string) =>
    apiFetch<Snapshot[]>(`/deals/${dealId}/snapshots`),

  get: (id: string) => apiFetch<Snapshot>(`/snapshots/${id}`),

  restore: (id: string) =>
    apiFetch<ExplorationSession>(`/snapshots/${id}/restore`, { method: "POST" }),

  delete: (id: string) =>
    apiFetch<void>(`/snapshots/${id}`, { method: "DELETE" }),
};
