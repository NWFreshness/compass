"use client";

import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

const TIER_COLORS = {
  tier1: "#34c97a",
  tier2: "#d99a30",
  tier3: "#d84a4a",
};

const TIER_LABELS = {
  tier1: "Tier 1",
  tier2: "Tier 2",
  tier3: "Tier 3",
};

interface TierDonutProps {
  distribution: { tier1: number; tier2: number; tier3: number };
}

export function TierDonut({ distribution }: TierDonutProps) {
  const data = (["tier1", "tier2", "tier3"] as const)
    .filter((t) => distribution[t] > 0)
    .map((t) => ({ name: TIER_LABELS[t], value: distribution[t], color: TIER_COLORS[t] }));

  if (data.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center text-xs text-muted-foreground">
        No data
      </div>
    );
  }

  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <ResponsiveContainer width="100%" height={140}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={36}
          outerRadius={54}
          strokeWidth={0}
          dataKey="value"
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "oklch(0.115 0.04 248)",
            border: "1px solid oklch(0.20 0.05 246)",
            borderRadius: "6px",
            color: "oklch(0.87 0.025 215)",
            fontSize: "12px",
          }}
          formatter={(value, name) => {
            const num = typeof value === "number" ? value : 0;
            return [`${num} (${Math.round((num / total) * 100)}%)`, name];
          }}
        />
        <Legend
          iconType="circle"
          iconSize={7}
          formatter={(value) => (
            <span style={{ fontSize: "11px", color: "oklch(0.60 0.04 225)" }}>{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
