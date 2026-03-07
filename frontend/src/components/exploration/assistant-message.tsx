"use client";

import type { ChatMessage } from "@/interfaces/api";

interface AssistantMessageProps {
  message: ChatMessage;
}

/**
 * Simple markdown-ish renderer: paragraphs, bold, headers, lists, code blocks.
 * We avoid pulling in a full markdown library for now.
 */
function renderMarkdown(text: string): React.ReactNode[] {
  const blocks = text.split(/\n\n+/);
  return blocks.map((block, i) => {
    const trimmed = block.trim();
    if (!trimmed) return null;

    // Code block
    if (trimmed.startsWith("```")) {
      const lines = trimmed.split("\n");
      // Remove opening ``` and closing ```
      const code = lines
        .slice(1, lines[lines.length - 1] === "```" ? -1 : undefined)
        .join("\n");
      return (
        <pre
          key={i}
          className="bg-muted rounded-md p-3 text-xs overflow-x-auto"
        >
          <code>{code}</code>
        </pre>
      );
    }

    // Header
    if (trimmed.startsWith("# ")) {
      return (
        <h3 key={i} className="text-base font-semibold">
          {trimmed.slice(2)}
        </h3>
      );
    }
    if (trimmed.startsWith("## ")) {
      return (
        <h4 key={i} className="text-sm font-semibold">
          {trimmed.slice(3)}
        </h4>
      );
    }
    if (trimmed.startsWith("### ")) {
      return (
        <h5 key={i} className="text-sm font-medium">
          {trimmed.slice(4)}
        </h5>
      );
    }

    // List (lines starting with -)
    const lines = trimmed.split("\n");
    if (lines.every((l) => l.trimStart().startsWith("- "))) {
      return (
        <ul key={i} className="list-disc list-inside space-y-0.5">
          {lines.map((line, j) => (
            <li key={j} className="text-sm">
              {renderInline(line.trimStart().slice(2))}
            </li>
          ))}
        </ul>
      );
    }

    // Regular paragraph
    return (
      <p key={i} className="text-sm">
        {lines.map((line, j) => (
          <span key={j}>
            {j > 0 && <br />}
            {renderInline(line)}
          </span>
        ))}
      </p>
    );
  });
}

/** Handle **bold** inline */
function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

export function AssistantMessage({ message }: AssistantMessageProps) {
  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] rounded-2xl rounded-bl-md bg-muted px-4 py-2.5 space-y-2">
        {renderMarkdown(message.content)}
      </div>
    </div>
  );
}
