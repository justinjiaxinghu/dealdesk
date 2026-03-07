"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

const CONNECTORS = [
  { id: "tavily", label: "TAVILY", enabled: true },
  { id: "costar", label: "COSTAR", enabled: false },
  { id: "compstack", label: "COMPSTACK", enabled: false },
  { id: "loopnet", label: "LOOPNET", enabled: false },
  { id: "rea_vista", label: "REA VISTA", enabled: false },
] as const;

interface SearchBarProps {
  onSearch: (query: string, connectors: string[]) => void;
  loading?: boolean;
}

export function SearchBar({ onSearch, loading = false }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set(["tavily"]));

  function toggleConnector(id: string) {
    const connector = CONNECTORS.find((c) => c.id === id);
    if (!connector?.enabled) return;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    onSearch(trimmed, Array.from(selected));
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {/* Connector chips */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs font-medium text-muted-foreground">
          Sources:
        </span>
        {CONNECTORS.map((c) => (
          <div key={c.id} className="relative group">
            <Badge
              variant={
                !c.enabled
                  ? "secondary"
                  : selected.has(c.id)
                    ? "default"
                    : "outline"
              }
              className={`cursor-pointer select-none text-xs ${
                !c.enabled
                  ? "opacity-40 cursor-not-allowed"
                  : "hover:opacity-80"
              }`}
              onClick={() => toggleConnector(c.id)}
            >
              {c.label}
            </Badge>
            {!c.enabled && (
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-foreground text-background text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                Coming soon
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Input + send */}
      <div className="flex items-center gap-2">
        <Input
          type="text"
          placeholder="Search for comparable properties, market data..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
          className="flex-1"
        />
        <Button type="submit" disabled={loading || !query.trim()}>
          {loading ? (
            <span className="flex items-center gap-2">
              <svg
                className="w-4 h-4 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Searching...
            </span>
          ) : (
            "Search"
          )}
        </Button>
      </div>
    </form>
  );
}
