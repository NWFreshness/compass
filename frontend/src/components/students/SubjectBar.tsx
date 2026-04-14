"use client";

interface SubjectBarProps {
  subjectName: string;
  average: number;
}

function barColor(score: number): string {
  if (score >= 80) return "bg-green-500";
  if (score >= 70) return "bg-yellow-400";
  return "bg-red-500";
}

function labelColor(score: number): string {
  if (score >= 80) return "text-green-700";
  if (score >= 70) return "text-yellow-700";
  return "text-red-700";
}

export function SubjectBar({ subjectName, average }: SubjectBarProps) {
  const pct = Math.min(Math.max(average, 0), 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{subjectName}</span>
        <span className={`text-sm font-semibold ${labelColor(average)}`}>{average.toFixed(1)}%</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor(average)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
