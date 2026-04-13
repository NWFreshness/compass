"use client";

import Link from "next/link";

import { TierBadge } from "@/components/dashboard/TierBadge";
import { TierDonut } from "@/components/dashboard/TierDonut";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { PrincipalDashboard as PrincipalDashboardData } from "@/lib/types";

interface PrincipalDashboardProps {
  data: PrincipalDashboardData;
}

export function PrincipalDashboard({ data }: PrincipalDashboardProps) {
  const { school_name, total_students, tier_distribution, classes, grade_averages, at_risk } = data;

  return (
    <div className="space-y-6 p-6">
      {/* School summary header */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle>{school_name}</CardTitle>
          <p className="text-sm text-slate-500">{total_students} students</p>
        </CardHeader>
        <CardContent>
          <TierDonut distribution={tier_distribution} />
        </CardContent>
      </Card>

      {/* Grade averages table */}
      {grade_averages.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Grade Averages</h2>
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Grade Level</TableHead>
                    <TableHead>Avg Score</TableHead>
                    <TableHead>Students</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {grade_averages.map((ga) => (
                    <TableRow key={ga.grade_level}>
                      <TableCell className="font-medium">Grade {ga.grade_level}</TableCell>
                      <TableCell>{ga.avg_score.toFixed(1)}</TableCell>
                      <TableCell>{ga.student_count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Class breakdown table */}
      <div className="space-y-2">
        <h2 className="text-lg font-semibold">Class Breakdown</h2>
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Class</TableHead>
                  <TableHead>Grade</TableHead>
                  <TableHead>Students</TableHead>
                  <TableHead>Avg Score</TableHead>
                  <TableHead>Tier Distribution</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {classes.map((cls) => (
                  <TableRow key={cls.id}>
                    <TableCell className="font-medium">{cls.name}</TableCell>
                    <TableCell>{cls.grade_level}</TableCell>
                    <TableCell>{cls.student_count}</TableCell>
                    <TableCell>
                      {cls.avg_score !== null ? cls.avg_score.toFixed(1) : "—"}
                    </TableCell>
                    <TableCell>
                      <TierDonut distribution={cls.tier_distribution} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* At-Risk Students panel */}
      {at_risk.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">At-Risk Students</h2>
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Class</TableHead>
                    <TableHead>Avg Score</TableHead>
                    <TableHead>Tier</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {at_risk.map((student) => (
                    <TableRow
                      key={student.student_id}
                      className={
                        student.tier === "tier3"
                          ? "bg-red-50"
                          : "bg-yellow-50"
                      }
                    >
                      <TableCell className="font-medium">
                        <Link href={`/students/${student.student_id}`} className="hover:underline">
                          {student.student_name}
                        </Link>
                      </TableCell>
                      <TableCell>{student.class_name}</TableCell>
                      <TableCell>{student.avg_score.toFixed(1)}</TableCell>
                      <TableCell>
                        <TierBadge tier={student.tier} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
