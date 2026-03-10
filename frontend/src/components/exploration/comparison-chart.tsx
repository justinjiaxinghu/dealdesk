"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";

interface ComparisonChartProps {
  data: { name: string; value: number }[];
  subjectValue?: number;
  label?: string;
}

export function ComparisonChart({
  data,
  subjectValue,
  label,
}: ComparisonChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">
        No data to display.
      </div>
    );
  }

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11 }}
            interval={0}
            angle={-30}
            textAnchor="end"
            height={60}
          />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid hsl(var(--border))",
            }}
          />
          <Bar
            dataKey="value"
            fill="hsl(var(--primary))"
            radius={[4, 4, 0, 0]}
            name={label || "Value"}
          />
          {subjectValue != null && (
            <ReferenceLine
              y={subjectValue}
              stroke="hsl(var(--destructive))"
              strokeDasharray="6 3"
              strokeWidth={2}
              label={{
                value: `Subject: ${subjectValue}`,
                position: "right",
                fontSize: 11,
                fill: "hsl(var(--destructive))",
              }}
            />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
