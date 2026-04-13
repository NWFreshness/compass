"use client";

import { useState } from "react";

import { AnalysisCard } from "@/components/ai/AnalysisCard";
import { AnalyzeButton } from "@/components/ai/AnalyzeButton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { AIRecommendation, Class } from "@/lib/types";

export function TeacherDashboard({ classes }: { classes: Class[] }) {
  const [classHistory, setClassHistory] = useState<Record<string, AIRecommendation[]>>({});
  const [loadingClassId, setLoadingClassId] = useState<string | null>(null);
  const [errorClassId, setErrorClassId] = useState<string | null>(null);

  async function handleAnalyzeClass(classId: string) {
    setLoadingClassId(classId);
    setErrorClassId(null);
    try {
      const created = await api.post<AIRecommendation>(`/ai/class/${classId}/analyze`);
      setClassHistory((current) => ({
        ...current,
        [classId]: [created, ...(current[classId] ?? [])],
      }));
    } catch {
      setErrorClassId(classId);
    } finally {
      setLoadingClassId(null);
    }
  }

  if (classes.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-slate-500">No classes assigned yet.</CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {classes.map((cls) => (
        <Card key={cls.id}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">{cls.name}</CardTitle>
                <p className="text-sm text-slate-500">Grade {cls.grade_level}</p>
              </div>
              <AnalyzeButton
                label="Analyze Class"
                loading={loadingClassId === cls.id}
                onClick={() => void handleAnalyzeClass(cls.id)}
              />
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {errorClassId === cls.id && (
              <p className="text-sm text-red-600">Failed to analyze class. Is Ollama running?</p>
            )}
            {classHistory[cls.id]?.[0] ? (
              <AnalysisCard recommendation={classHistory[cls.id][0]} />
            ) : (
              <p className="text-sm text-slate-400">No recommendation yet. Click Analyze Class to generate one.</p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
