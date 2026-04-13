"use client";

import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

const TIER_COLORS = {
  tier1: "#22c55e",
  tier2: "#eab308",
  tier3: "#ef4444",
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
    return <div className="flex h-32 items-center justify-center text-sm text-slate-400">No data</div>;
  }

  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <ResponsiveContainer width="100%" height={140}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={35}
          outerRadius={55}
          dataKey="value"
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value, name) => {
            const num = typeof value === "number" ? value : 0;
            return [`${num} (${Math.round((num / total) * 100)}%)`, name];
          }}
        />
        <Legend iconType="circle" iconSize={8} />
      </PieChart>
    </ResponsiveContainer>
  );
}
