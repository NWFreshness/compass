"use client";

import { Button } from "@/components/ui/button";

export function AnalyzeButton({
  label,
  loading,
  onClick,
}: {
  label: string;
  loading: boolean;
  onClick: () => void;
}) {
  return (
    <Button onClick={onClick} disabled={loading} size="sm">
      {loading ? "Analyzing..." : label}
    </Button>
  );
}
