import { apiFetch } from "./api-client";
import type { Dataset } from "@/interfaces/api";

export const datasetService = {
  create: (data: { name: string; deal_id?: string | null; properties?: Record<string, unknown>[] }) =>
    apiFetch<Dataset>("/datasets", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  list: () => apiFetch<Dataset[]>("/datasets"),

  listFree: () => apiFetch<Dataset[]>("/datasets/free"),

  listByDeal: (dealId: string) =>
    apiFetch<Dataset[]>(`/deals/${dealId}/datasets`),

  get: (id: string) => apiFetch<Dataset>(`/datasets/${id}`),

  update: (id: string, data: { name?: string; deal_id?: string | null; properties?: Record<string, unknown>[] }) =>
    apiFetch<Dataset>(`/datasets/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  addProperties: (id: string, properties: Record<string, unknown>[]) =>
    apiFetch<Dataset>(`/datasets/${id}/properties`, {
      method: "POST",
      body: JSON.stringify({ properties }),
    }),

  delete: (id: string) =>
    apiFetch<void>(`/datasets/${id}`, { method: "DELETE" }),
};
