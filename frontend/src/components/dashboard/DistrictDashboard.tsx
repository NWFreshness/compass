"use client";

import { TierDonut } from "@/components/dashboard/TierDonut";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { DistrictDashboard as DistrictDashboardData } from "@/lib/types";

interface DistrictDashboardProps {
  data: DistrictDashboardData;
}

export function DistrictDashboard({ data }: DistrictDashboardProps) {
  const { total_students, tier_distribution, schools } = data;

  return (
    <div className="space-y-6 p-6">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle>District Overview</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center gap-6">
          <div>
            <p className="text-3xl font-bold">{total_students}</p>
            <p className="text-sm text-slate-500">total students</p>
          </div>
          <TierDonut distribution={tier_distribution} />
        </CardContent>
      </Card>

      <div className="space-y-2">
        <h2 className="text-lg font-semibold">Schools</h2>
        {schools.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-sm text-slate-500">No schools found.</CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>School Name</TableHead>
                    <TableHead>Students</TableHead>
                    <TableHead>Avg Score</TableHead>
                    <TableHead>Tier Distribution</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {schools.map((school) => (
                    <TableRow key={school.id} className={school.high_risk ? "bg-red-50" : undefined}>
                      <TableCell className="font-medium">{school.name}</TableCell>
                      <TableCell>{school.student_count}</TableCell>
                      <TableCell>
                        {school.avg_score !== null ? school.avg_score.toFixed(1) : "—"}
                      </TableCell>
                      <TableCell>
                        <TierDonut distribution={school.tier_distribution} />
                      </TableCell>
                      <TableCell>
                        {school.high_risk && (
                          <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-700">
                            High Risk
                          </span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
