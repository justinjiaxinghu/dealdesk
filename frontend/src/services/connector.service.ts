import { apiFetch } from "./api-client";
import type { Connector } from "@/interfaces/api";

export const connectorService = {
  async list(): Promise<Connector[]> {
    return apiFetch<Connector[]>("/connectors");
  },
  async connect(provider: string): Promise<Connector> {
    return apiFetch<Connector>(`/connectors/${provider}/connect`, {
      method: "POST",
    });
  },
  async disconnect(provider: string): Promise<Connector> {
    return apiFetch<Connector>(`/connectors/${provider}/disconnect`, {
      method: "POST",
    });
  },
};
