"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { connectorService } from "@/services/connector.service";
import type { Connector } from "@/interfaces/api";

const PROVIDER_META: Record<string, { label: string; description: string }> = {
  onedrive: {
    label: "OneDrive",
    description: "Microsoft OneDrive and SharePoint personal files",
  },
  box: {
    label: "Box",
    description: "Box cloud storage and collaboration",
  },
  google_drive: {
    label: "Google Drive",
    description: "Google Drive documents and folders",
  },
  sharepoint: {
    label: "SharePoint",
    description: "Microsoft SharePoint team sites",
  },
};

export default function ConnectorsPage() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    connectorService
      .list()
      .then(setConnectors)
      .catch((err) => console.error("Failed to load connectors", err))
      .finally(() => setLoading(false));
  }, []);

  async function handleToggle(connector: Connector) {
    setActionLoading(connector.provider);
    try {
      const updated =
        connector.status === "connected"
          ? await connectorService.disconnect(connector.provider)
          : await connectorService.connect(connector.provider);
      setConnectors((prev) =>
        prev.map((c) => (c.provider === updated.provider ? updated : c))
      );
    } catch (err) {
      console.error("Failed to toggle connector", err);
    } finally {
      setActionLoading(null);
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Connectors</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Connect external file storage providers to search your documents
          during market exploration.
        </p>
      </div>

      {loading ? (
        <div className="text-muted-foreground">Loading connectors...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {connectors.map((connector) => {
            const meta = PROVIDER_META[connector.provider] ?? {
              label: connector.provider,
              description: "",
            };
            const isConnected = connector.status === "connected";
            const isToggling = actionLoading === connector.provider;

            return (
              <Card key={connector.provider}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{meta.label}</CardTitle>
                    <Badge variant={isConnected ? "default" : "secondary"}>
                      {isConnected ? "Connected" : "Not Connected"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    {meta.description}
                  </p>
                  {isConnected && (
                    <p className="text-xs text-muted-foreground">
                      {connector.file_count} files indexed
                    </p>
                  )}
                  <Button
                    variant={isConnected ? "outline" : "default"}
                    size="sm"
                    disabled={isToggling}
                    onClick={() => handleToggle(connector)}
                  >
                    {isToggling
                      ? "..."
                      : isConnected
                        ? "Disconnect"
                        : "Connect"}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
