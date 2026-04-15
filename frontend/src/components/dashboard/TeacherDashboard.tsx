"use client";

import { AtRiskStudentsTable } from "@/components/dashboard/AtRiskStudentsTable";
import { ClassInterventionPanel } from "@/components/interventions/ClassInterventionPanel";
import { TierBadge } from "@/components/dashboard/TierBadge";
import { TierDonut } from "@/components/dashboard/TierDonut";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TeacherDashboard as TeacherDashboardData } from "@/lib/types";

interface TeacherDashboardProps {
  data: TeacherDashboardData;
}

export function TeacherDashboard({ data }: TeacherDashboardProps) {
  const { classes, at_risk } = data;

  if (classes.length === 0) {
    return (
      <div className="space-y-4 p-6">
        <Card>
          <CardContent className="p-6 text-sm text-slate-500">No classes assigned.</CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {classes.map((cls) => (
            <Card key={cls.id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">{cls.name}</CardTitle>
              <p className="text-sm text-slate-500">Grade {cls.grade_level}</p>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-4 text-sm">
                <span>
                  <span className="font-medium">{cls.student_count}</span>{" "}
                  <span className="text-slate-500">students</span>
                </span>
                <span>
                  <span className="font-medium">
                    {cls.avg_score !== null ? cls.avg_score.toFixed(1) : "—"}
                  </span>{" "}
                  <span className="text-slate-500">avg score</span>
                </span>
              </div>
              <TierDonut distribution={cls.tier_distribution} />
              <div className="flex flex-wrap gap-2 text-xs text-slate-600">
                <span>
                  <span className="font-medium">{cls.tier_distribution.tier1}</span>{" "}
                  <TierBadge tier="tier1" />
                </span>
                <span className="text-slate-300">·</span>
                <span>
                  <span className="font-medium">{cls.tier_distribution.tier2}</span>{" "}
                  <TierBadge tier="tier2" />
                </span>
                <span className="text-slate-300">·</span>
                <span>
                  <span className="font-medium">{cls.tier_distribution.tier3}</span>{" "}
                  <TierBadge tier="tier3" />
                </span>
              </div>
              <ClassInterventionPanel
                classId={cls.id}
                className={cls.name}
                gradeLevel={cls.grade_level}
                compact
              />
            </CardContent>
          </Card>
        ))}
      </div>

      {at_risk.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">At-Risk Students</h2>
          <AtRiskStudentsTable students={at_risk} />
        </div>
      )}
    </div>
  );
}
