"use client";

const TIER_STYLES = {
  tier1: {
    bg: "bg-emerald-500/10 dark:bg-emerald-500/10",
    text: "text-emerald-600 dark:text-emerald-400",
    border: "border border-emerald-500/20 dark:border-emerald-500/20",
    label: "Tier 1",
  },
  tier2: {
    bg: "bg-amber-500/10 dark:bg-amber-500/10",
    text: "text-amber-600 dark:text-amber-400",
    border: "border border-amber-500/20 dark:border-amber-500/20",
    label: "Tier 2",
  },
  tier3: {
    bg: "bg-red-500/10 dark:bg-red-500/10",
    text: "text-red-600 dark:text-red-400",
    border: "border border-red-500/20 dark:border-red-500/20",
    label: "Tier 3",
  },
} as const;

interface TierBadgeProps {
  tier: "tier1" | "tier2" | "tier3";
}

export function TierBadge({ tier }: TierBadgeProps) {
  const { bg, text, border, label } = TIER_STYLES[tier];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium tabular-nums ${bg} ${text} ${border}`}
    >
      {label}
    </span>
  );
}
