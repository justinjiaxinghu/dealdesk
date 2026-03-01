// frontend/src/services/validation.service.ts
// Field validation operations.

import type { FieldValidation } from "@/interfaces/api";
import { apiFetch } from "./api-client";

export const validationService = {
  /** Run OM field validation for a deal. Optionally specify phase: "quick" or "deep". */
  async validate(dealId: string, phase?: "quick" | "deep"): Promise<FieldValidation[]> {
    const url = phase
      ? `/deals/${dealId}/validate?phase=${phase}`
      : `/deals/${dealId}/validate`;
    return apiFetch<FieldValidation[]>(url, {
      method: "POST",
      body: JSON.stringify({}),
    });
  },

  /** List existing validations for a deal. */
  async list(dealId: string): Promise<FieldValidation[]> {
    return apiFetch<FieldValidation[]>(
      `/deals/${dealId}/validations`,
    );
  },
};
