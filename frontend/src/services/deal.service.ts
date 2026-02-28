// frontend/src/services/deal.service.ts
// CRUD operations for deals.

import type { CreateDealInput, Deal } from "@/interfaces/api";
import { apiFetch } from "./api-client";

export const dealService = {
  /** Create a new deal. */
  async create(input: CreateDealInput): Promise<Deal> {
    return apiFetch<Deal>("/deals", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  /** List all deals, optionally filtered. */
  async list(filters?: {
    property_type?: string;
    status?: string;
    city?: string;
  }): Promise<Deal[]> {
    const params = new URLSearchParams();
    if (filters?.property_type)
      params.set("property_type", filters.property_type);
    if (filters?.status) params.set("status_filter", filters.status);
    if (filters?.city) params.set("city", filters.city);
    const qs = params.toString();
    return apiFetch<Deal[]>(`/deals${qs ? `?${qs}` : ""}`);
  },

  /** Get a single deal by ID. */
  async get(dealId: string): Promise<Deal> {
    return apiFetch<Deal>(`/deals/${dealId}`);
  },

  /** Partially update a deal. */
  async update(
    dealId: string,
    data: Partial<CreateDealInput>,
  ): Promise<Deal> {
    return apiFetch<Deal>(`/deals/${dealId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },
};
