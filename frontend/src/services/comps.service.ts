// frontend/src/services/comps.service.ts
import type { Comp } from "@/interfaces/api";
import { apiFetch } from "./api-client";

export const compsService = {
  /** Fetch (or re-fetch) comparable properties for a deal. Stores results to DB. */
  async search(dealId: string): Promise<Comp[]> {
    return apiFetch<Comp[]>(`/deals/${dealId}/comps:search`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  },

  /** List cached comps for a deal. */
  async list(dealId: string): Promise<Comp[]> {
    return apiFetch<Comp[]>(`/deals/${dealId}/comps`);
  },
};
