"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AnalysisCard } from "@/components/ai/AnalysisCard";
import { AnalysisHistory } from "@/components/ai/AnalysisHistory";
import { AnalyzeButton } from "@/components/ai/AnalyzeButton";
import { TierBadge } from "@/components/dashboard/TierBadge";
import { InterventionForm } from "@/components/interventions/InterventionForm";
import { InterventionList } from "@/components/interventions/InterventionList";
import { Header } from "@/components/layout/header";
import { SubjectBar } from "@/components/students/SubjectBar";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AIRecommendation, Intervention, Score, Student, Subject } from "@/lib/types";

function sortInterventions(items: Intervention[]) {
  return [...items].sort((a, b) => {
    if (a.status !== b.status) return a.status.localeCompare(b.status);
    return b.start_date.localeCompare(a.start_date);
  });
}

function scoreCellClass(value: number): string {
  if (value >= 80) return "font-semibold text-green-700 bg-green-50 dark:bg-green-950 dark:text-green-300";
  if (value >= 70) return "font-semibold text-yellow-700 bg-yellow-50 dark:bg-yellow-950 dark:text-yellow-300";
  return "font-semibold text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300";
}

export default function StudentDetailPage() {
  const params = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const [student, setStudent] = useState<Student | null>(null);
  const [scores, setScores] = useState<Score[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [history, setHistory] = useState<AIRecommendation[]>([]);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [loading, setLoading] = useState(true);
  const [streamingText, setStreamingText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState("");
  const [showInterventionForm, setShowInterventionForm] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [studentData, scoreData, subjectData, aiHistory, interventionData] = await Promise.all([
          api.get<Student>(`/students/${params.id}`),
          api.get<Score[]>(`/scores/student/${params.id}`),
          api.get<Subject[]>("/lookups/subjects"),
          api.get<AIRecommendation[]>(`/ai/student/${params.id}/history`),
          api.get<Intervention[]>(`/interventions?student_id=${params.id}`),
        ]);
        setStudent(studentData);
        setScores(scoreData);
        setSubjects(subjectData);
        setHistory(aiHistory);
        setInterventions(sortInterventions(interventionData));
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load student profile");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [params.id]);

  async function handleAnalyzeStudent() {
    setIsStreaming(true);
    setStreamingText("");
    setError("");
    await api.postStream(
      `/ai/student/${params.id}/analyze/stream`,
      (token) => setStreamingText((prev) => prev + token),
      async (_recId) => {
        setIsStreaming(false);
        try {
          const updated = await api.get<AIRecommendation[]>(`/ai/student/${params.id}/history`);
          setHistory(updated);
          setStreamingText("");
        } catch {
          setError("Analysis saved but failed to refresh history");
        }
      },
      (msg) => {
        setIsStreaming(false);
        setStreamingText("");
        setError(msg || "Analysis failed");
      },
    );
  }

  function handleInterventionCreated(intervention: Intervention) {
    setInterventions((current) => sortInterventions([intervention, ...current]));
    setShowInterventionForm(false);
  }

  function handleInterventionUpdated(updated: Intervention) {
    setInterventions((current) =>
      sortInterventions(current.map((i) => (i.id === updated.id ? updated : i)))
    );
  }

  async function handleExport(fmt: "csv" | "pdf") {
    try {
      const res = await fetch(`/api/reports/student/${params.id}?format=${fmt}`, { credentials: "include" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `student_report.${fmt}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Export failed");
    }
  }

  const subjectNames = useMemo(
    () => Object.fromEntries(subjects.map((s) => [s.id, s.name])),
    [subjects]
  );

  const subjectAverages = useMemo(() => {
    const grouped: Record<string, number[]> = {};
    for (const score of scores) {
      if (!grouped[score.subject_id]) grouped[score.subject_id] = [];
      grouped[score.subject_id].push(score.value);
    }
    return Object.entries(grouped)
      .map(([subjectId, values]) => ({
        subjectId,
        name: subjectNames[subjectId] ?? subjectId,
        average: values.reduce((a, b) => a + b, 0) / values.length,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [scores, subjectNames]);

  const overallTier = useMemo(() => {
    if (scores.length === 0) return null;
    const avg = scores.reduce((a, b) => a + b.value, 0) / scores.length;
    if (avg >= 80) return "tier1" as const;
    if (avg >= 70) return "tier2" as const;
    return "tier3" as const;
  }, [scores]);

  return (
    <div>
      <Header title={student ? student.name : "Student Profile"} />
      <div className="space-y-4 p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Link href="/students" className={buttonVariants({ variant: "outline" })}>
            Back to Students
          </Link>
          {student && (
            <div className="flex gap-1">
              <button type="button" className={buttonVariants({ variant: "outline", size: "sm" })} onClick={() => void handleExport("csv")}>
                Export CSV
              </button>
              <button type="button" className={buttonVariants({ variant: "outline", size: "sm" })} onClick={() => void handleExport("pdf")}>
                Export PDF
              </button>
            </div>
          )}
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
            ))}
          </div>
        ) : error ? (
          <Card>
            <CardContent className="p-6 text-sm text-red-600">{error}</CardContent>
          </Card>
        ) : student ? (
          <>
            <Card>
              <CardContent className="grid gap-4 p-6 sm:grid-cols-4">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Student ID</p>
                  <p className="mt-1 font-medium">{student.student_id_number}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Grade</p>
                  <p className="mt-1 font-medium">Grade {student.grade_level}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Scores Recorded</p>
                  <p className="mt-1 font-medium">{scores.length}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">MTSS Tier</p>
                  <div className="mt-1">{overallTier ? <TierBadge tier={overallTier} /> : <span className="text-slate-400 text-sm">No scores</span>}</div>
                </div>
              </CardContent>
            </Card>

            {subjectAverages.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Subject Performance</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 p-6 pt-0">
                  {subjectAverages.map((s) => (
                    <SubjectBar key={s.subjectId} subjectName={s.name} average={s.average} />
                  ))}
                </CardContent>
              </Card>
            )}

            <Card>
              <CardContent className="space-y-4 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">AI Recommendation</p>
                    <p className="text-sm text-slate-500">Generate benchmark-aware support guidance for this student.</p>
                  </div>
                  <AnalyzeButton label="Analyze Student" loading={isStreaming} onClick={() => void handleAnalyzeStudent()} />
                </div>
                {isStreaming && streamingText ? (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base">Analyzing...</CardTitle>
                    </CardHeader>
                    <CardContent className="text-sm">
                      <p className="whitespace-pre-wrap text-slate-700 dark:text-slate-300">{streamingText}</p>
                    </CardContent>
                  </Card>
                ) : history[0] ? (
                  <AnalysisCard recommendation={history[0]} />
                ) : null}
                {history.length > 1 && (
                  <div>
                    <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">History</p>
                    <AnalysisHistory items={history.slice(1)} />
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Score History</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {scores.length === 0 ? (
                  <div className="p-6 text-sm text-slate-500">No scores recorded for this student yet.</div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Subject</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Score</TableHead>
                        <TableHead>Notes</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {scores.map((score) => (
                        <TableRow key={score.id}>
                          <TableCell className="text-sm">{score.date}</TableCell>
                          <TableCell className="text-sm">{subjectNames[score.subject_id] ?? score.subject_id}</TableCell>
                          <TableCell className="capitalize text-sm">{score.score_type}</TableCell>
                          <TableCell className={`rounded-md px-2 py-1 text-sm ${scoreCellClass(score.value)}`}>{score.value}%</TableCell>
                          <TableCell className="text-sm text-slate-500">{score.notes || "\u2014"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardContent className="space-y-4 p-6">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-medium">Interventions</p>
                    <p className="text-sm text-slate-500">Track active supports and resolution notes for this student.</p>
                  </div>
                  {!authLoading && user ? (
                    <button
                      type="button"
                      className={buttonVariants({ variant: showInterventionForm ? "outline" : "default" })}
                      onClick={() => setShowInterventionForm((current) => !current)}
                    >
                      {showInterventionForm ? "Cancel" : "Add Intervention"}
                    </button>
                  ) : null}
                </div>
                {showInterventionForm && user ? (
                  <div className="rounded-lg border border-slate-200 p-4">
                    <InterventionForm target={{ type: "student", id: params.id }} onCreated={handleInterventionCreated} onCancel={() => setShowInterventionForm(false)} />
                  </div>
                ) : null}
                {user ? (
                  <InterventionList interventions={interventions} userRole={user.role} onUpdated={handleInterventionUpdated} />
                ) : (
                  <p className="text-sm text-slate-500">Loading intervention permissions...</p>
                )}
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    </div>
  );
}
