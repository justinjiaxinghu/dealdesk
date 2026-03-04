import { apiFetch } from "./api-client";
import type {
  ProjectionResult,
  SensitivityRequest,
  SensitivityResponse,
} from "@/interfaces/api";

export const financialModelService = {
  compute: (dealId: string): Promise<ProjectionResult> =>
    apiFetch<ProjectionResult>(`/deals/${dealId}/financial-model:compute`, {
      method: "POST",
    }),

  sensitivity: (dealId: string, body: SensitivityRequest): Promise<SensitivityResponse> =>
    apiFetch<SensitivityResponse>(`/deals/${dealId}/sensitivity`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
