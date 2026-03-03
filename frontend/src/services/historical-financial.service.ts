import { apiFetch } from "./api-client";
import type { HistoricalFinancial } from "@/interfaces/api";

export const historicalFinancialService = {
  list: (dealId: string): Promise<HistoricalFinancial[]> =>
    apiFetch<HistoricalFinancial[]>(`/deals/${dealId}/historical-financials`),

  extract: (dealId: string, documentId: string): Promise<HistoricalFinancial[]> =>
    apiFetch<HistoricalFinancial[]>(
      `/deals/${dealId}/documents/${documentId}/historical-financials:extract`,
      { method: "POST" }
    ),
};
