// frontend/src/services/export.service.ts
// Excel export operations.

import type { ExportRecord } from "@/interfaces/api";
import { apiFetch } from "./api-client";

export const exportService = {
  /** Export an assumption set result to XLSX. */
  async exportXlsx(setId: string): Promise<ExportRecord> {
    return apiFetch<ExportRecord>(
      `/assumption-sets/${setId}/export/xlsx`,
      { method: "POST" },
    );
  },
};
