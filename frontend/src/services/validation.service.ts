// frontend/src/services/validation.service.ts
// Field validation operations.

import type { FieldValidation } from "@/interfaces/api";
import { apiFetch } from "./api-client";

export const validationService = {
  /** Run OM field validation for a deal. */
  async validate(dealId: string): Promise<FieldValidation[]> {
    return apiFetch<FieldValidation[]>(
      `/deals/${dealId}/validate`,
      {
        method: "POST",
        body: JSON.stringify({}),
      },
    );
  },

  /** List existing validations for a deal. */
  async list(dealId: string): Promise<FieldValidation[]> {
    return apiFetch<FieldValidation[]>(
      `/deals/${dealId}/validations`,
    );
  },
};
