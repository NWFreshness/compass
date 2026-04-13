"use client";

import { useState } from "react";

import { AnalysisCard } from "@/components/ai/AnalysisCard";
import { AnalyzeButton } from "@/components/ai/AnalyzeButton";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import type { AIRecommendation, Class } from "@/lib/types";

export function PrincipalDashboard({ classes }: { classes: Class[] }) {
  const [classHistory, setClassHistory] = useState<Record<string, AIRecommendation[]>>({});
  const [loadingClassId, setLoadingClassId] = useState<string | null>(null);

  async function handleAnalyzeClass(classId: string) {
    setLoadingClassId(classId);
    try {
      const created = await api.post<AIRecommendation>(`/ai/class/${classId}/analyze`);
      setClassHistory((current) => ({
        ...current,
        [classId]: [created, ...(current[classId] ?? [])],
      }));
    } finally {
      setLoadingClassId(null);
    }
  }

  if (classes.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-slate-500">No classes found for this school.</CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Class</TableHead>
                <TableHead>Grade</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {classes.map((cls) => (
                <>
                  <TableRow key={cls.id}>
                    <TableCell className="font-medium">{cls.name}</TableCell>
                    <TableCell>Grade {cls.grade_level}</TableCell>
                    <TableCell className="text-right">
                      <AnalyzeButton
                        label="Analyze Class"
                        loading={loadingClassId === cls.id}
                        onClick={() => void handleAnalyzeClass(cls.id)}
                      />
                    </TableCell>
                  </TableRow>
                  {classHistory[cls.id]?.[0] && (
                    <TableRow key={`${cls.id}-rec`}>
                      <TableCell colSpan={3} className="bg-slate-50 py-2">
                        <AnalysisCard recommendation={classHistory[cls.id][0]} />
                      </TableCell>
                    </TableRow>
                  )}
                </>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
