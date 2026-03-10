"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { Dataset } from "@/interfaces/api";
import { datasetService } from "@/services/dataset.service";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    datasetService
      .list()
      .then(setDatasets)
      .catch((err) => console.error("Failed to load datasets", err))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await datasetService.delete(id);
      setDatasets((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      console.error("Failed to delete dataset", err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Datasets</h1>
      </div>

      {loading ? (
        <div className="text-muted-foreground">Loading datasets...</div>
      ) : datasets.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground mb-2">No datasets yet.</p>
          <p className="text-sm text-muted-foreground">
            Search for properties in{" "}
            <Link href="/explore" className="text-blue-600 hover:underline">
              Explore
            </Link>{" "}
            or a deal workspace, then click &quot;Add to Dataset&quot; on
            results.
          </p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Properties</TableHead>
              <TableHead>Context</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {datasets.map((ds) => (
              <TableRow
                key={ds.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => router.push(`/datasets/${ds.id}`)}
              >
                <TableCell className="font-medium">{ds.name}</TableCell>
                <TableCell>
                  <Badge variant="secondary">
                    {ds.properties.length}{" "}
                    {ds.properties.length === 1 ? "property" : "properties"}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {ds.deal_id ? "Deal-linked" : "Standalone"}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {new Date(ds.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <button
                    className="p-1 rounded text-muted-foreground hover:text-red-600 hover:bg-red-50 transition-colors"
                    onClick={(e) => handleDelete(ds.id, e)}
                    title="Delete dataset"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
