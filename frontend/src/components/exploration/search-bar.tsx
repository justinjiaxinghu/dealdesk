"use client";

import { useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";

interface SearchBarProps {
  onSearch: (query: string, connectors: string[]) => void;
  onUploadOM?: (file: File) => void;
  loading?: boolean;
  connectedSources?: string[];
}

export function SearchBar({ onSearch, onUploadOM, loading = false, connectedSources }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set(["tavily"]));
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const connectorChips = [
    { id: "tavily", label: "WEB SEARCH", enabled: true },
    ...["onedrive", "box", "google_drive", "sharepoint"].map((p) => ({
      id: p,
      label: p.replace("_", " ").toUpperCase(),
      enabled: connectedSources?.includes(p) ?? false,
    })),
  ];

  function toggleConnector(id: string) {
    const connector = connectorChips.find((c) => c.id === id);
    if (!connector?.enabled) return;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function handleSubmit() {
    const trimmed = query.trim();
    if (!trimmed || loading) return;
    onSearch(trimmed, Array.from(selected));
    setQuery("");
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function handleInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setQuery(e.target.value);
    // Auto-resize
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 150) + "px";
  }

  const canSend = query.trim().length > 0 && !loading;

  return (
    <div className="border-t bg-background px-4 py-3">
      {/* Connector chips */}
      <div className="flex items-center gap-1.5 mb-2 flex-wrap">
        <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
          Sources:
        </span>
        {connectorChips.map((c) => (
          <div key={c.id} className="relative group">
            <Badge
              variant={
                !c.enabled
                  ? "secondary"
                  : selected.has(c.id)
                    ? "default"
                    : "outline"
              }
              className={`cursor-pointer select-none text-[10px] px-1.5 py-0 ${
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

      {/* Input area with send button */}
      <div className="relative flex items-end gap-2">
        <textarea
          ref={textareaRef}
          rows={1}
          placeholder="Ask about comparable properties, market data..."
          value={query}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={loading}
          className="flex-1 resize-none rounded-xl border border-input bg-muted/30 px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1 disabled:opacity-50"
          style={{ minHeight: "42px", maxHeight: "150px" }}
        />
        {onUploadOM && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  onUploadOM(file);
                  e.target.value = "";
                }
              }}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
              className="flex items-center justify-center w-9 h-9 rounded-full border border-input text-muted-foreground shrink-0 transition-opacity hover:text-foreground hover:border-foreground disabled:opacity-30 disabled:cursor-not-allowed mb-0.5"
              aria-label="Upload Offering Memorandum"
              title="Upload Offering Memorandum"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v11a2 2 0 002 2z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 11v6m-3-3l3-3 3 3" />
              </svg>
            </button>
          </>
        )}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!canSend}
          className="flex items-center justify-center w-9 h-9 rounded-full bg-foreground text-background shrink-0 transition-opacity disabled:opacity-30 hover:opacity-80 disabled:cursor-not-allowed mb-0.5"
          aria-label="Send message"
        >
          {loading ? (
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
          ) : (
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 10l7-7m0 0l7 7m-7-7v18"
              />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
