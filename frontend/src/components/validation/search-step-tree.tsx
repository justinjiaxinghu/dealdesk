"use client";

import type { SearchStep } from "@/interfaces/api";

interface SearchStepTreeProps {
  steps: SearchStep[];
}

export function SearchStepTree({ steps }: SearchStepTreeProps) {
  const quickSteps = steps.filter((s) => s.phase === "quick");
  const deepSteps = steps.filter((s) => s.phase === "deep");

  if (steps.length === 0) {
    return (
      <p className="text-muted-foreground text-xs">No search steps recorded.</p>
    );
  }

  return (
    <div className="space-y-0">
      {/* Quick Search Phase */}
      {quickSteps.length > 0 && (
        <div className="border-l-4 border-blue-400 bg-blue-50 rounded-r-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-700">
              Quick Search
            </span>
            <span className="text-xs text-blue-500">
              {quickSteps.length} {quickSteps.length === 1 ? "query" : "queries"}
            </span>
          </div>
          <div className="space-y-3">
            {quickSteps.map((step, i) => (
              <SearchQuery key={`quick-${i}`} step={step} />
            ))}
          </div>
        </div>
      )}

      {/* Connector */}
      {quickSteps.length > 0 && deepSteps.length > 0 && (
        <div className="flex justify-start pl-5">
          <div className="w-0.5 h-6 bg-gray-300" />
        </div>
      )}

      {/* Deep Search Phase */}
      {deepSteps.length > 0 && (
        <div className="border-l-4 border-green-500 bg-green-50 rounded-r-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-green-700">
              Deep Search
            </span>
            <span className="text-xs text-green-600">
              {deepSteps.length} {deepSteps.length === 1 ? "query" : "queries"}
            </span>
          </div>
          <div className="space-y-3">
            {deepSteps.map((step, i) => (
              <SearchQuery key={`deep-${i}`} step={step} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SearchQuery({ step }: { step: SearchStep }) {
  return (
    <div className="text-sm">
      <div className="flex items-start gap-1.5">
        <span className="text-muted-foreground shrink-0">{"\uD83D\uDD0D"}</span>
        <span className="font-medium text-foreground">&ldquo;{step.query}&rdquo;</span>
      </div>
      {step.results.length > 0 && (
        <div className="ml-6 mt-1 space-y-0.5">
          {step.results.map((r, i) => (
            <a
              key={i}
              href={r.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-xs text-blue-600 hover:underline truncate"
              title={r.snippet}
            >
              {"\u2192"} {r.title || r.url}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
