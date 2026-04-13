"use client";

const TIER_STYLES = {
  tier1: { bg: "bg-green-100 text-green-800", label: "Tier 1" },
  tier2: { bg: "bg-yellow-100 text-yellow-800", label: "Tier 2" },
  tier3: { bg: "bg-red-100 text-red-800", label: "Tier 3" },
} as const;

interface TierBadgeProps {
  tier: "tier1" | "tier2" | "tier3";
}

export function TierBadge({ tier }: TierBadgeProps) {
  const { bg, label } = TIER_STYLES[tier];
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${bg}`}>
      {label}
    </span>
  );
}
