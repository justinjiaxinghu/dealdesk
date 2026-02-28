// frontend/src/services/document.service.ts
// Document upload, listing, and extraction retrieval.

import type {
  Document,
  ExtractedField,
  MarketTable,
  QuickExtractResult,
} from "@/interfaces/api";
import { apiFetch, apiUpload } from "./api-client";

export const documentService = {
  /** Upload a PDF document for a deal. */
  async upload(dealId: string, file: File): Promise<Document> {
    const formData = new FormData();
    formData.append("file", file);
    return apiUpload<Document>(`/deals/${dealId}/documents`, formData);
  },

  /** List all documents for a deal. */
  async list(dealId: string): Promise<Document[]> {
    return apiFetch<Document[]>(`/deals/${dealId}/documents`);
  },

  /** Get a single document by ID. */
  async get(dealId: string, documentId: string): Promise<Document> {
    return apiFetch<Document>(
      `/deals/${dealId}/documents/${documentId}`,
    );
  },

  /** Get extracted fields for a document. */
  async getFields(
    dealId: string,
    documentId: string,
  ): Promise<ExtractedField[]> {
    return apiFetch<ExtractedField[]>(
      `/deals/${dealId}/documents/${documentId}/fields`,
    );
  },

  /** Get extracted market tables for a document. */
  async getTables(
    dealId: string,
    documentId: string,
  ): Promise<MarketTable[]> {
    return apiFetch<MarketTable[]>(
      `/deals/${dealId}/documents/${documentId}/tables`,
    );
  },

  /** Quick-extract basic deal info from a PDF (lightweight, pre-submit). */
  async quickExtract(file: File): Promise<QuickExtractResult> {
    const formData = new FormData();
    formData.append("file", file);
    return apiUpload<QuickExtractResult>(`/documents/quick-extract`, formData);
  },
};
