// frontend/src/services/assumption.service.ts
// Assumption sets, assumptions, and benchmark generation.

import type {
  Assumption,
  AssumptionSet,
  Benchmark,
} from "@/interfaces/api";
import { apiFetch } from "./api-client";

export interface BulkAssumptionInput {
  key: string;
  value_number: number | null;
  unit: string | null;
  range_min: number | null;
  range_max: number | null;
  source_type: string;
  source_ref: string | null;
  notes: string | null;
}

export const assumptionService = {
  /** List assumption sets for a deal. */
  async listSets(dealId: string): Promise<AssumptionSet[]> {
    return apiFetch<AssumptionSet[]>(
      `/deals/${dealId}/assumption-sets`,
    );
  },

  /** List assumptions within an assumption set. */
  async listAssumptions(setId: string): Promise<Assumption[]> {
    return apiFetch<Assumption[]>(
      `/assumption-sets/${setId}/assumptions`,
    );
  },

  /** Bulk-update (upsert) assumptions in an assumption set. */
  async bulkUpdate(
    setId: string,
    assumptions: BulkAssumptionInput[],
  ): Promise<Assumption[]> {
    return apiFetch<Assumption[]>(
      `/assumption-sets/${setId}/assumptions`,
      {
        method: "PUT",
        body: JSON.stringify({ assumptions }),
      },
    );
  },

  /** Generate AI-powered benchmarks for a deal. */
  async generateBenchmarks(dealId: string): Promise<Benchmark[]> {
    return apiFetch<Benchmark[]>(
      `/deals/${dealId}/benchmarks:generate`,
      {
        method: "POST",
        body: JSON.stringify({}),
      },
    );
  },
};
