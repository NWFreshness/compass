import type { AIRecommendation } from "@/lib/types";

const TIER_LABEL: Record<string, string> = {
  tier1: "Tier 1",
  tier2: "Tier 2",
  tier3: "Tier 3",
};

export function AnalysisHistory({ items }: { items: AIRecommendation[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-slate-500">No recommendation history yet.</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.id} className="rounded-md border p-3 text-sm">
          <p className="font-medium">{new Date(item.created_at).toLocaleString()}</p>
          <p className="text-slate-500">
            Tier: {TIER_LABEL[item.snapshot.recommended_tier] ?? item.snapshot.recommended_tier}
          </p>
          <p className="mt-2 whitespace-pre-wrap text-slate-700">{item.response}</p>
        </div>
      ))}
    </div>
  );
}
