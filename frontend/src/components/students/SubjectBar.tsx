"use client";

interface SubjectBarProps {
  subjectName: string;
  average: number;
}

function barColor(score: number): string {
  if (score >= 80) return "#34c97a";
  if (score >= 70) return "#d99a30";
  return "#d84a4a";
}

function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-500 dark:text-emerald-400";
  if (score >= 70) return "text-amber-500 dark:text-amber-400";
  return "text-red-500 dark:text-red-400";
}

export function SubjectBar({ subjectName, average }: SubjectBarProps) {
  const pct = Math.min(Math.max(average, 0), 100);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-foreground/80">{subjectName}</span>
        <span className={`text-sm font-semibold tabular-nums font-mono ${scoreColor(average)}`}>
          {average.toFixed(1)}%
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%`, background: barColor(average) }}
        />
      </div>
    </div>
  );
}
