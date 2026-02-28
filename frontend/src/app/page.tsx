"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
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

function statusBadgeVariant(status: string) {
  switch (status.toLowerCase()) {
    case "active":
      return "bg-green-100 text-green-800";
    case "closed":
      return "bg-gray-100 text-gray-800";
    case "draft":
      return "bg-yellow-100 text-yellow-800";
    default:
      return "bg-blue-100 text-blue-800";
  }
}

export default function DealsPage() {
  const { deals, loading } = useDeals();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Deals</h1>
        <Link href="/deals/new">
          <Button>New Deal</Button>
        </Link>
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
              <TableHead>Status</TableHead>
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
                  <Badge
                    className={statusBadgeVariant(deal.status)}
                  >
                    {deal.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  {new Date(deal.created_at).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
