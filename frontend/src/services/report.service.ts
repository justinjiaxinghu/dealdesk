import { apiFetch, apiUpload } from "./api-client";
import type { ReportTemplate, ReportJob } from "@/interfaces/api";

export const reportService = {
  async uploadTemplate(file: File): Promise<ReportTemplate> {
    const formData = new FormData();
    formData.append("file", file);
    return apiUpload<ReportTemplate>("/report-templates", formData);
  },
  async listTemplates(): Promise<ReportTemplate[]> {
    return apiFetch<ReportTemplate[]>("/report-templates");
  },
  async getTemplate(id: string): Promise<ReportTemplate> {
    return apiFetch<ReportTemplate>(`/report-templates/${id}`);
  },
  async createJob(templateId: string, name: string): Promise<ReportJob> {
    return apiFetch<ReportJob>("/report-jobs", {
      method: "POST",
      body: JSON.stringify({ template_id: templateId, name }),
    });
  },
  async updateFills(
    jobId: string,
    fills: Record<string, unknown>,
  ): Promise<ReportJob> {
    return apiFetch<ReportJob>(`/report-jobs/${jobId}`, {
      method: "PATCH",
      body: JSON.stringify({ fills }),
    });
  },
  async aiFill(
    jobId: string,
    connectors: string[],
    prompt?: string,
  ): Promise<ReportJob> {
    return apiFetch<ReportJob>(`/report-jobs/${jobId}/ai-fill`, {
      method: "POST",
      body: JSON.stringify({ connectors, prompt }),
    });
  },
  async generate(jobId: string): Promise<ReportJob> {
    return apiFetch<ReportJob>(`/report-jobs/${jobId}/generate`, {
      method: "POST",
    });
  },
  async listJobs(): Promise<ReportJob[]> {
    return apiFetch<ReportJob[]>("/report-jobs");
  },
  downloadUrl(jobId: string): string {
    const base =
      process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/v1";
    return `${base}/report-jobs/${jobId}/download`;
  },
};
