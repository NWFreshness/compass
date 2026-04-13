import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AIRecommendation } from "@/lib/types";

const TIER_LABEL: Record<string, string> = {
  tier1: "Tier 1 (On Track)",
  tier2: "Tier 2 (Some Risk)",
  tier3: "Tier 3 (At Risk)",
};

function stripMarkdown(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, "$1")  // **bold** → bold
    .replace(/^[*-]\s+/gm, "• ");      // * item / - item → • item
}

export function AnalysisCard({ recommendation }: { recommendation: AIRecommendation }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Latest Recommendation</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <p>
          <span className="font-medium">Recommended tier:</span>{" "}
          {TIER_LABEL[recommendation.snapshot.recommended_tier] ?? recommendation.snapshot.recommended_tier}
        </p>
        <p>
          <span className="font-medium">Model:</span> {recommendation.model_name}
        </p>
        {recommendation.parse_error && (
          <p className="text-amber-600 text-xs">{recommendation.parse_error}</p>
        )}
        <p className="whitespace-pre-wrap text-slate-700">{stripMarkdown(recommendation.response)}</p>
      </CardContent>
    </Card>
  );
}
