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
import { useDeals } from "@/hooks/use-deal";
import { explorationService } from "@/services/exploration.service";
import type { ExplorationSession } from "@/interfaces/api";


export default function DealsPage() {
  const { deals, loading } = useDeals();
  const router = useRouter();

  const [explorations, setExplorations] = useState<ExplorationSession[]>([]);
  const [explorationsLoading, setExplorationsLoading] = useState(true);

  useEffect(() => {
    explorationService
      .list()
      .then(setExplorations)
      .catch((err) => console.error("Failed to load explorations", err))
      .finally(() => setExplorationsLoading(false));
  }, []);

  // Build a map of deal_id -> deal name for quick lookup
  const dealNameMap = new Map(deals.map((d) => [d.id, d.name]));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Deals</h1>
        <div className="flex items-center gap-2">
          <Link href="/explore">
            <Button variant="outline">Explore Market</Button>
          </Link>
          <Link href="/deals/new">
            <Button>New Deal</Button>
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="text-muted-foreground">Loading deals...</div>
      ) : deals.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground mb-4">No deals yet.</p>
          <Link href="/deals/new">
            <Button>Create your first deal</Button>
          </Link>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Address</TableHead>
              <TableHead>Property Type</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {deals.map((deal) => (
              <TableRow key={deal.id}>
                <TableCell>
                  <Link
                    href={`/deals/${deal.id}`}
                    className="text-blue-600 hover:underline font-medium"
                  >
                    {deal.name}
                  </Link>
                </TableCell>
                <TableCell>
                  {deal.address}, {deal.city}, {deal.state}
                </TableCell>
                <TableCell>{deal.property_type}</TableCell>
                <TableCell>
                  {new Date(deal.created_at).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Saved Explorations */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Saved Explorations</h2>
        {explorationsLoading ? (
          <div className="text-muted-foreground">Loading explorations...</div>
        ) : explorations.length === 0 ? (
          <div className="text-muted-foreground">No saved explorations yet</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Deal</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {explorations.map((exp) => (
                <TableRow
                  key={exp.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() =>
                    router.push(
                      exp.deal_id
                        ? `/deals/${exp.deal_id}`
                        : `/explore?exploration=${exp.id}`
                    )
                  }
                >
                  <TableCell className="font-medium">{exp.name}</TableCell>
                  <TableCell>
                    {exp.deal_id
                      ? dealNameMap.get(exp.deal_id) ?? "Unknown Deal"
                      : "Free"}
                  </TableCell>
                  <TableCell>
                    {new Date(exp.created_at).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
