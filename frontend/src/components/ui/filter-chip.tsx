"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface FilterChipProps {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
  /** If provided, uses these as display labels for options (must match options length) */
  optionLabels?: string[];
}

function fuzzyMatch(query: string, text: string): boolean {
  const q = query.toLowerCase();
  const t = text.toLowerCase();
  if (t.includes(q)) return true;
  // Simple fuzzy: all query chars appear in order
  let qi = 0;
  for (let ti = 0; ti < t.length && qi < q.length; ti++) {
    if (t[ti] === q[qi]) qi++;
  }
  return qi === q.length;
}

function fuzzyScore(query: string, text: string): number {
  const q = query.toLowerCase();
  const t = text.toLowerCase();
  if (t === q) return 3;
  if (t.startsWith(q)) return 2;
  if (t.includes(q)) return 1;
  return 0;
}

export function FilterChip({
  label,
  value,
  options,
  onChange,
  optionLabels,
}: FilterChipProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setQuery("");
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  const filtered = useMemo(() => {
    const items = options.map((opt, i) => ({
      value: opt,
      label: optionLabels?.[i] ?? opt,
    }));
    if (!query) return items;
    return items
      .filter((item) => fuzzyMatch(query, item.label))
      .sort((a, b) => fuzzyScore(query, b.label) - fuzzyScore(query, a.label));
  }, [options, optionLabels, query]);

  const displayValue = useMemo(() => {
    if (!value) return null;
    const idx = options.indexOf(value);
    return idx >= 0 && optionLabels ? optionLabels[idx] : value;
  }, [value, options, optionLabels]);

  const handleSelect = useCallback(
    (val: string) => {
      onChange(val);
      setOpen(false);
    },
    [onChange]
  );

  const handleClear = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onChange("");
      setOpen(false);
    },
    [onChange]
  );

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm transition-colors hover:bg-muted/50 cursor-pointer ${
            value
              ? "border-blue-300 bg-blue-50 text-blue-800"
              : "border-border bg-background text-muted-foreground"
          }`}
        >
          <span className="font-medium">{label}:</span>
          <span>{displayValue || "Any"}</span>
          {value && (
            <span
              onClick={handleClear}
              className="ml-0.5 hover:text-red-600 cursor-pointer"
            >
              ×
            </span>
          )}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-0" align="start">
        <div className="p-2 border-b">
          <input
            ref={inputRef}
            type="text"
            placeholder={`Search ${label.toLowerCase()}...`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full text-sm outline-none bg-transparent placeholder:text-muted-foreground"
          />
        </div>
        <div className="max-h-48 overflow-y-auto p-1">
          {filtered.length === 0 ? (
            <div className="px-2 py-3 text-sm text-muted-foreground text-center">
              No matches
            </div>
          ) : (
            filtered.map((item) => (
              <button
                key={item.value}
                onClick={() => handleSelect(item.value)}
                className={`w-full text-left px-2 py-1.5 text-sm rounded-sm hover:bg-muted cursor-pointer ${
                  item.value === value ? "bg-muted font-medium" : ""
                }`}
              >
                {item.label}
              </button>
            ))
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
