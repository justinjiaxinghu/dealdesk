"use client";

import type { ChatMessage } from "@/interfaces/api";

interface AssistantMessageProps {
  message: ChatMessage;
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
  // Handle links and bold
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

export function AssistantMessage({ message }: AssistantMessageProps) {
  // Skip empty assistant messages (tool-call-only intermediaries)
  if (!message.content || message.content.trim() === "") return null;

  return (
    <div className="flex justify-start">
      <div className="max-w-[90%] rounded-2xl rounded-bl-md bg-muted px-4 py-3 space-y-3">
        {renderMarkdown(message.content)}
      </div>
    </div>
  );
}
