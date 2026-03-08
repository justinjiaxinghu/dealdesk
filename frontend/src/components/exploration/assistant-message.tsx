"use client";

import { useCallback, useEffect, useState } from "react";
import type { ChatMessage, Dataset } from "@/interfaces/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { datasetService } from "@/services/dataset.service";

interface AssistantMessageProps {
  message: ChatMessage;
  dealId?: string | null;
}

interface PropertyData {
  address: string;
  property_type?: string;
  cap_rate?: number;
  rent_per_unit?: number;
  rent_per_sqft?: number;
  sale_price?: number;
  noi?: number;
  year_built?: number;
  unit_count?: number;
  square_feet?: number;
  occupancy_rate?: number;
  vacancy_rate?: number;
  expense_ratio?: number;
  opex_per_unit?: number;
  price_per_unit?: number;
  price_per_sqft?: number;
  capex?: number;
  capex_per_unit?: number;
  debt_service?: number;
  dscr?: number;
  source_url?: string;
  notes?: string;
  [key: string]: unknown;
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

/** Extract ```properties JSON block from content, return [textWithout, properties] */
function extractProperties(content: string): [string, PropertyData[]] {
  const regex = /```properties\s*\n([\s\S]*?)```/;
  const match = content.match(regex);
  if (!match) return [content, []];

  const textWithout = content.replace(regex, "").trim();
  try {
    const parsed = JSON.parse(match[1]);
    if (Array.isArray(parsed)) return [textWithout, parsed];
  } catch {
    // invalid JSON, ignore
  }
  return [content, []];
}

/** Build metrics array from property data — used for both card and modal */
function buildCardMetrics(property: PropertyData) {
  const metrics: { label: string; value: string }[] = [];
  if (property.cap_rate != null)
    metrics.push({ label: "Cap Rate", value: formatPercent(property.cap_rate) });
  if (property.noi != null)
    metrics.push({ label: "NOI", value: formatCurrency(property.noi) });
  if (property.sale_price != null)
    metrics.push({ label: "Sale Price", value: formatCurrency(property.sale_price) });
  if (property.rent_per_unit != null)
    metrics.push({ label: "Rent/Unit", value: `$${property.rent_per_unit.toLocaleString()}` });
  return metrics;
}

function buildAllMetrics(property: PropertyData) {
  const sections: { title: string; items: { label: string; value: string }[] }[] = [];

  // Pricing
  const pricing: { label: string; value: string }[] = [];
  if (property.sale_price != null) pricing.push({ label: "Sale Price", value: formatCurrency(property.sale_price) });
  if (property.price_per_unit != null) pricing.push({ label: "Price/Unit", value: formatCurrency(property.price_per_unit) });
  if (property.price_per_sqft != null) pricing.push({ label: "Price/SF", value: `$${property.price_per_sqft.toFixed(2)}` });
  if (property.cap_rate != null) pricing.push({ label: "Cap Rate", value: formatPercent(property.cap_rate) });
  if (pricing.length > 0) sections.push({ title: "Pricing", items: pricing });

  // Income
  const income: { label: string; value: string }[] = [];
  if (property.noi != null) income.push({ label: "NOI", value: formatCurrency(property.noi) });
  if (property.rent_per_unit != null) income.push({ label: "Rent/Unit", value: `$${property.rent_per_unit.toLocaleString()}` });
  if (property.rent_per_sqft != null) income.push({ label: "Rent/SF", value: `$${property.rent_per_sqft.toFixed(2)}` });
  if (property.occupancy_rate != null) income.push({ label: "Occupancy", value: formatPercent(property.occupancy_rate) });
  if (property.vacancy_rate != null) income.push({ label: "Vacancy", value: formatPercent(property.vacancy_rate) });
  if (income.length > 0) sections.push({ title: "Income", items: income });

  // Expenses
  const expenses: { label: string; value: string }[] = [];
  if (property.expense_ratio != null) expenses.push({ label: "Expense Ratio", value: formatPercent(property.expense_ratio) });
  if (property.opex_per_unit != null) expenses.push({ label: "OpEx/Unit", value: formatCurrency(property.opex_per_unit) });
  if (property.capex != null) expenses.push({ label: "CapEx", value: formatCurrency(property.capex) });
  if (property.capex_per_unit != null) expenses.push({ label: "CapEx/Unit", value: formatCurrency(property.capex_per_unit) });
  if (expenses.length > 0) sections.push({ title: "Expenses", items: expenses });

  // Debt
  const debt: { label: string; value: string }[] = [];
  if (property.debt_service != null) debt.push({ label: "Debt Service", value: formatCurrency(property.debt_service) });
  if (property.dscr != null) debt.push({ label: "DSCR", value: property.dscr.toFixed(2) + "x" });
  if (debt.length > 0) sections.push({ title: "Debt", items: debt });

  // Physical
  const physical: { label: string; value: string }[] = [];
  if (property.unit_count != null) physical.push({ label: "Units", value: property.unit_count.toString() });
  if (property.square_feet != null) physical.push({ label: "Sq Ft", value: property.square_feet.toLocaleString() });
  if (property.year_built != null) physical.push({ label: "Year Built", value: property.year_built.toString() });
  if (physical.length > 0) sections.push({ title: "Physical", items: physical });

  return sections;
}

function PropertyCard({
  property,
  onClick,
}: {
  property: PropertyData;
  onClick: () => void;
}) {
  const metrics = buildCardMetrics(property);

  return (
    <Card
      className="transition-shadow hover:shadow-md cursor-pointer"
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-sm leading-tight">
            {property.address}
          </CardTitle>
          {property.property_type && (
            <Badge variant="secondary" className="text-xs shrink-0">
              {property.property_type}
            </Badge>
          )}
        </div>
      </CardHeader>
      {metrics.length > 0 && (
        <CardContent className="pt-0">
          <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
            {metrics.map((m) => (
              <div key={m.label} className="flex justify-between text-xs">
                <span className="text-muted-foreground">{m.label}</span>
                <span className="font-medium">{m.value}</span>
              </div>
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

function PropertyDetailModal({
  property,
  open,
  onOpenChange,
}: {
  property: PropertyData | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  if (!property) return null;

  const sections = buildAllMetrics(property);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-start gap-3">
            <span className="leading-tight">{property.address}</span>
            {property.property_type && (
              <Badge variant="secondary" className="text-xs shrink-0 mt-0.5">
                {property.property_type}
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {sections.map((section) => (
            <div key={section.title}>
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                {section.title}
              </h4>
              <div className="grid grid-cols-2 gap-x-6 gap-y-2">
                {section.items.map((item) => (
                  <div
                    key={item.label}
                    className="flex justify-between text-sm"
                  >
                    <span className="text-muted-foreground">{item.label}</span>
                    <span className="font-medium">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {sections.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No detailed metrics available for this property.
            </p>
          )}

          {property.notes && (
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Notes
              </h4>
              <p className="text-sm">{property.notes}</p>
            </div>
          )}

          {property.source_url && (
            <a
              href={property.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:underline"
            >
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
              View Source
            </a>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Simple markdown-ish renderer: paragraphs, bold, headers, lists, code blocks, tables.
 */
function renderMarkdown(text: string): React.ReactNode[] {
  const blocks = text.split(/\n\n+/);
  const nodes: React.ReactNode[] = [];

  for (let i = 0; i < blocks.length; i++) {
    const trimmed = blocks[i].trim();
    if (!trimmed) continue;

    // Code block
    if (trimmed.startsWith("```")) {
      const lines = trimmed.split("\n");
      const code = lines
        .slice(1, lines[lines.length - 1] === "```" ? -1 : undefined)
        .join("\n");
      nodes.push(
        <pre key={i} className="bg-muted rounded-md p-3 text-xs overflow-x-auto">
          <code>{code}</code>
        </pre>
      );
      continue;
    }

    // Table: detect lines with | separators
    const lines = trimmed.split("\n");
    if (
      lines.length >= 2 &&
      lines[0].includes("|") &&
      lines[1].match(/^\|?[\s-:|]+\|/)
    ) {
      const tableNode = renderTable(lines, i);
      if (tableNode) {
        nodes.push(tableNode);
        continue;
      }
    }

    // Header
    if (trimmed.startsWith("### ")) {
      nodes.push(<h5 key={i} className="text-sm font-medium">{trimmed.slice(4)}</h5>);
      continue;
    }
    if (trimmed.startsWith("## ")) {
      nodes.push(<h4 key={i} className="text-sm font-semibold">{trimmed.slice(3)}</h4>);
      continue;
    }
    if (trimmed.startsWith("# ")) {
      nodes.push(<h3 key={i} className="text-base font-semibold">{trimmed.slice(2)}</h3>);
      continue;
    }

    // List (lines starting with - or numbered)
    if (lines.every((l) => l.trimStart().startsWith("- ") || l.trimStart().match(/^\d+\.\s/))) {
      nodes.push(
        <ul key={i} className="list-disc list-inside space-y-0.5">
          {lines.map((line, j) => (
            <li key={j} className="text-sm">
              {renderInline(line.trimStart().replace(/^[-\d]+[\.\)]\s*/, ""))}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Regular paragraph
    nodes.push(
      <p key={i} className="text-sm">
        {lines.map((line, j) => (
          <span key={j}>
            {j > 0 && <br />}
            {renderInline(line)}
          </span>
        ))}
      </p>
    );
  }

  return nodes;
}

/** Render a markdown table */
function renderTable(lines: string[], key: number): React.ReactNode | null {
  const parseRow = (line: string) =>
    line
      .split("|")
      .map((cell) => cell.trim())
      .filter((cell) => cell.length > 0 && !cell.match(/^[-:]+$/));

  const headerCells = parseRow(lines[0]);
  if (headerCells.length === 0) return null;

  // Skip separator line (line 1)
  const bodyRows = lines.slice(2).filter((l) => l.includes("|"));

  return (
    <div key={key} className="overflow-x-auto rounded-md border">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-muted/50">
            {headerCells.map((cell, j) => (
              <th
                key={j}
                className="px-3 py-2 text-left font-medium text-muted-foreground border-b"
              >
                {renderInline(cell)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bodyRows.map((row, ri) => {
            const cells = parseRow(row);
            return (
              <tr key={ri} className="border-b last:border-0 hover:bg-muted/30">
                {headerCells.map((_, ci) => (
                  <td key={ci} className="px-3 py-2">
                    {renderInline(cells[ci] || "")}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/** Handle **bold** and [links](url) inline */
function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      return (
        <a
          key={i}
          href={linkMatch[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          {linkMatch[1]}
        </a>
      );
    }
    return part;
  });
}

function AddToDatasetButton({
  properties,
  dealId,
}: {
  properties: PropertyData[];
  dealId?: string | null;
}) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [showMenu, setShowMenu] = useState(false);
  const [creating, setCreating] = useState(false);
  const [adding, setAdding] = useState<string | null>(null);
  const [showNameInput, setShowNameInput] = useState(false);
  const [newName, setNewName] = useState("");

  const loadDatasets = useCallback(async () => {
    try {
      const ds = dealId
        ? await datasetService.listByDeal(dealId)
        : await datasetService.listFree();
      setDatasets(ds);
    } catch {
      // ignore
    }
  }, [dealId]);

  useEffect(() => {
    if (showMenu) loadDatasets();
  }, [showMenu, loadDatasets]);

  const handleCreateNew = async () => {
    const name = newName.trim() || `Search Results ${new Date().toLocaleDateString()}`;
    setCreating(true);
    try {
      await datasetService.create({
        name,
        deal_id: dealId || undefined,
        properties: properties as Record<string, unknown>[],
      });
      setShowMenu(false);
      setShowNameInput(false);
      setNewName("");
    } catch (err) {
      console.error("Failed to create dataset", err);
    } finally {
      setCreating(false);
    }
  };

  const handleAddToExisting = async (datasetId: string) => {
    setAdding(datasetId);
    try {
      await datasetService.addProperties(
        datasetId,
        properties as Record<string, unknown>[]
      );
      setShowMenu(false);
    } catch (err) {
      console.error("Failed to add to dataset", err);
    } finally {
      setAdding(null);
    }
  };

  return (
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        className="text-xs"
        onClick={() => {
          setShowMenu(!showMenu);
          if (showMenu) {
            setShowNameInput(false);
            setNewName("");
          }
        }}
      >
        <svg
          className="w-3.5 h-3.5 mr-1"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 4v16m8-8H4"
          />
        </svg>
        Add to Dataset
      </Button>
      {showMenu && (
        <div className="absolute bottom-full left-0 mb-1 bg-background border rounded-md shadow-lg z-50 w-64 py-1">
          {showNameInput ? (
            <div className="px-3 py-2 space-y-2">
              <input
                className="w-full text-sm border rounded px-2 py-1.5 bg-background outline-none focus:ring-1 focus:ring-ring"
                placeholder="Dataset name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCreateNew();
                  if (e.key === "Escape") {
                    setShowNameInput(false);
                    setNewName("");
                  }
                }}
                autoFocus
              />
              <div className="flex gap-1.5">
                <Button
                  size="sm"
                  className="text-xs flex-1"
                  onClick={handleCreateNew}
                  disabled={creating}
                >
                  {creating ? "Creating..." : "Create"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs"
                  onClick={() => {
                    setShowNameInput(false);
                    setNewName("");
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <button
              className="w-full text-left px-3 py-2 text-sm hover:bg-muted flex items-center gap-2"
              onClick={() => setShowNameInput(true)}
            >
              <svg
                className="w-4 h-4 text-muted-foreground"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 4v16m8-8H4"
                />
              </svg>
              New Dataset
            </button>
          )}
          {datasets.length > 0 && (
            <div className="border-t my-1" />
          )}
          {datasets.map((ds) => (
            <button
              key={ds.id}
              className="w-full text-left px-3 py-2 text-sm hover:bg-muted disabled:opacity-50 truncate"
              onClick={() => handleAddToExisting(ds.id)}
              disabled={adding === ds.id}
            >
              {adding === ds.id ? "Adding..." : ds.name}
              <span className="text-xs text-muted-foreground ml-1">
                ({ds.properties.length})
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function AssistantMessage({ message, dealId }: AssistantMessageProps) {
  const [selectedProperty, setSelectedProperty] = useState<PropertyData | null>(
    null
  );

  // Skip empty assistant messages (tool-call-only intermediaries)
  if (!message.content || message.content.trim() === "") return null;

  const [textContent, properties] = extractProperties(message.content);

  return (
    <div className="flex justify-start">
      <div className="max-w-[90%] rounded-2xl rounded-bl-md bg-muted px-4 py-3 space-y-3">
        {renderMarkdown(textContent)}

        {properties.length > 0 && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              {properties.map((prop, i) => (
                <PropertyCard
                  key={i}
                  property={prop}
                  onClick={() => setSelectedProperty(prop)}
                />
              ))}
            </div>
            <div className="flex justify-end pt-1">
              <AddToDatasetButton
                properties={properties}
                dealId={dealId}
              />
            </div>
          </>
        )}
      </div>

      <PropertyDetailModal
        property={selectedProperty}
        open={selectedProperty !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedProperty(null);
        }}
      />
    </div>
  );
}
