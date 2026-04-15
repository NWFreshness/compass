"use client";

import Link from "next/link";

import { TierBadge } from "@/components/dashboard/TierBadge";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { AtRiskStudent } from "@/lib/types";

interface AtRiskStudentsTableProps {
  students: AtRiskStudent[];
}

function getRowClassName(tier: AtRiskStudent["tier"]) {
  if (tier === "tier3") {
    return "bg-red-50";
  }
  if (tier === "tier2") {
    return "bg-yellow-50";
  }
  return undefined;
}

export function AtRiskStudentsTable({ students }: AtRiskStudentsTableProps) {
  if (students.length === 0) {
    return null;
  }

  return (
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
            {students.map((student) => (
              <TableRow key={student.student_id} className={getRowClassName(student.tier)}>
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
  );
}
