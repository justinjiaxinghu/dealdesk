// frontend/src/services/model.service.ts
// Financial model compute and result retrieval.

import type { ModelResult } from "@/interfaces/api";
import { apiFetch } from "./api-client";

export const modelService = {
  /** Trigger model computation for an assumption set. */
  async compute(setId: string): Promise<ModelResult> {
    return apiFetch<ModelResult>(
      `/assumption-sets/${setId}/compute`,
      { method: "POST" },
    );
  },

  /** Get the latest model result for an assumption set. */
  async getResult(setId: string): Promise<ModelResult> {
    return apiFetch<ModelResult>(
      `/assumption-sets/${setId}/result`,
    );
  },
};
