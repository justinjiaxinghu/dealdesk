// frontend/src/services/export.service.ts
// Excel export operations.

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/v1";

export const exportService = {
  /** Download the XLSX file for an assumption set. */
  downloadXlsx(setId: string): void {
    const url = `${API_BASE}/assumption-sets/${setId}/export/xlsx`;
    window.open(url, "_blank");
  },
};
