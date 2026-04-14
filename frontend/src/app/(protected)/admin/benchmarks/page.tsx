"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { BenchmarkForm, type BenchmarkSubmitPayload } from "@/components/admin/BenchmarkForm";
import { BenchmarkTable } from "@/components/admin/BenchmarkTable";
import { Header } from "@/components/layout/header";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Benchmark, BenchmarkFormValues, Subject } from "@/lib/types";

const DEFAULT_TIER1_MIN = 80;
const DEFAULT_TIER2_MIN = 70;
const ALL_GRADES = "all-grades";
const ALL_SUBJECTS = "all-subjects";

function toFormValues(benchmark?: Benchmark): BenchmarkFormValues {
  if (!benchmark) {
    return {
      grade_level: "",
      subject_id: "",
      tier1_min: String(DEFAULT_TIER1_MIN),
      tier2_min: String(DEFAULT_TIER2_MIN),
    };
  }

  return {
    grade_level: String(benchmark.grade_level),
    subject_id: benchmark.subject_id,
    tier1_min: String(benchmark.tier1_min),
    tier2_min: String(benchmark.tier2_min),
  };
}

export default function BenchmarksAdminPage() {
  const { user } = useAuth();
  const canManage = user?.role === "it_admin" || user?.role === "district_admin";
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [gradeFilter, setGradeFilter] = useState(ALL_GRADES);
  const [subjectFilter, setSubjectFilter] = useState(ALL_SUBJECTS);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingBenchmark, setEditingBenchmark] = useState<Benchmark | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const loadRequestIdRef = useRef(0);

  const sortedBenchmarks = useMemo(
    () =>
      [...benchmarks].sort((left, right) => {
        if (left.grade_level !== right.grade_level) {
          return left.grade_level - right.grade_level;
        }

        const leftSubject = subjects.find((subject) => subject.id === left.subject_id)?.name ?? left.subject_id;
        const rightSubject = subjects.find((subject) => subject.id === right.subject_id)?.name ?? right.subject_id;
        return leftSubject.localeCompare(rightSubject);
      }),
    [benchmarks, subjects]
  );

  const createInitialValues = useMemo(() => toFormValues(), []);
  const editInitialValues = useMemo(() => toFormValues(editingBenchmark ?? undefined), [editingBenchmark]);

  const loadSubjects = useCallback(async () => {
    return api.get<Subject[]>("/lookups/subjects");
  }, []);

  const loadBenchmarks = useCallback(async (activeGradeFilter = gradeFilter, activeSubjectFilter = subjectFilter) => {
    const params = new URLSearchParams();
    if (activeGradeFilter !== ALL_GRADES) {
      params.set("grade_level", activeGradeFilter);
    }
    if (activeSubjectFilter !== ALL_SUBJECTS) {
      params.set("subject_id", activeSubjectFilter);
    }

    const query = params.toString();
    const path = query ? `/benchmarks?${query}` : "/benchmarks";
    return api.get<Benchmark[]>(path);
  }, [gradeFilter, subjectFilter]);

  const refresh = useCallback(async (activeGradeFilter = gradeFilter, activeSubjectFilter = subjectFilter) => {
    const requestId = ++loadRequestIdRef.current;
    setLoading(true);
    setLoadError("");

    try {
      const [subjectData, benchmarkData] = await Promise.all([
        loadSubjects(),
        loadBenchmarks(activeGradeFilter, activeSubjectFilter),
      ]);

      if (requestId !== loadRequestIdRef.current) {
        return;
      }

      setSubjects(subjectData);
      setBenchmarks(benchmarkData);
    } catch (err: unknown) {
      if (requestId !== loadRequestIdRef.current) {
        return;
      }

      setLoadError(err instanceof Error ? err.message : "Unable to load benchmark overrides");
    } finally {
      if (requestId === loadRequestIdRef.current) {
        setLoading(false);
      }
    }
  }, [gradeFilter, loadBenchmarks, loadSubjects, subjectFilter]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function handleCreate(payload: BenchmarkSubmitPayload) {
    setSubmitError("");
    setIsSubmitting(true);

    try {
      await api.post("/benchmarks", payload);
      setIsCreateOpen(false);
      await refresh();
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : "Unable to create benchmark override");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleUpdate(payload: BenchmarkSubmitPayload) {
    if (!editingBenchmark) {
      return;
    }

    setSubmitError("");
    setIsSubmitting(true);

    try {
      await api.patch(`/benchmarks/${editingBenchmark.id}`, {
        tier1_min: payload.tier1_min,
        tier2_min: payload.tier2_min,
      });
      setEditingBenchmark(null);
      await refresh();
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : "Unable to update benchmark override");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete(benchmark: Benchmark) {
    if (!window.confirm("Delete this benchmark override and return to default thresholds for this grade and subject?")) {
      return;
    }

    setDeleteError("");
    setDeletingId(benchmark.id);

    try {
      await api.delete(`/benchmarks/${benchmark.id}`);
      await refresh();
    } catch (err: unknown) {
      setDeleteError(err instanceof Error ? err.message : "Unable to delete benchmark override");
    } finally {
      setDeletingId(null);
    }
  }

  async function handleGradeFilterChange(value: string | null) {
    const nextValue = value ?? ALL_GRADES;
    setGradeFilter(nextValue);
  }

  async function handleSubjectFilterChange(value: string | null) {
    const nextValue = value ?? ALL_SUBJECTS;
    setSubjectFilter(nextValue);
  }

  return (
    <div>
      <Header title="Benchmark Thresholds" />
      <div className="space-y-4 p-6">
        <Card>
          <CardHeader className="gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-1">
              <CardTitle>MTSS Benchmark Overrides</CardTitle>
              <CardDescription>
                Create grade-and-subject overrides for tier thresholds. Missing rows fall back to the default thresholds.
              </CardDescription>
            </div>
            {canManage ? (
              <Dialog
                open={isCreateOpen}
                onOpenChange={(open) => {
                  setIsCreateOpen(open);
                  if (!open) {
                    setSubmitError("");
                  }
                }}
              >
                <DialogTrigger render={<Button>Add Override</Button>} />
                <DialogContent className="sm:max-w-lg">
                  <DialogHeader>
                    <DialogTitle>New Benchmark Override</DialogTitle>
                  </DialogHeader>
                  <BenchmarkForm
                    key={`create-${isCreateOpen ? "open" : "closed"}`}
                    mode="create"
                    subjects={subjects}
                    initialValues={createInitialValues}
                    error={submitError}
                    submitting={isSubmitting}
                    onSubmit={handleCreate}
                    onCancel={() => {
                      setIsCreateOpen(false);
                      setSubmitError("");
                    }}
                  />
                </DialogContent>
              </Dialog>
            ) : null}
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <AlertTitle>Default fallback</AlertTitle>
              <AlertDescription>
                When no override exists for a grade and subject, MTSS calculations use Tier 1 at {DEFAULT_TIER1_MIN}
                and Tier 2 at {DEFAULT_TIER2_MIN}.
              </AlertDescription>
            </Alert>

            {!canManage ? (
              <Alert>
                <AlertTitle>Read-only access</AlertTitle>
                <AlertDescription>
                  Only IT admins and district admins can create, edit, or delete benchmark overrides.
                </AlertDescription>
              </Alert>
            ) : null}

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <span className="text-sm font-medium">Grade Filter</span>
                <Select value={gradeFilter} onValueChange={(value) => void handleGradeFilterChange(value)}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="All grades">
                      {(value: string) => (value === ALL_GRADES ? "All grades" : `Grade ${value}`)}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={ALL_GRADES}>All grades</SelectItem>
                    {Array.from({ length: 12 }, (_, index) => String(index + 1)).map((grade) => (
                      <SelectItem key={grade} value={grade}>
                        Grade {grade}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <span className="text-sm font-medium">Subject Filter</span>
                <Select value={subjectFilter} onValueChange={(value) => void handleSubjectFilterChange(value)}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="All subjects">
                      {(value: string) =>
                        value === ALL_SUBJECTS
                          ? "All subjects"
                          : (subjects.find((subject) => subject.id === value)?.name ?? value)
                      }
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={ALL_SUBJECTS}>All subjects</SelectItem>
                    {subjects.map((subject) => (
                      <SelectItem key={subject.id} value={subject.id}>
                        {subject.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {loadError ? (
              <Alert variant="destructive">
                <AlertTitle>Unable to load benchmark overrides</AlertTitle>
                <AlertDescription>{loadError}</AlertDescription>
              </Alert>
            ) : null}

            {deleteError ? (
              <Alert variant="destructive">
                <AlertTitle>Delete failed</AlertTitle>
                <AlertDescription>{deleteError}</AlertDescription>
              </Alert>
            ) : null}

            <Card className="py-0">
              <CardContent className="p-0">
                {loading ? (
                  <div className="px-4 py-8 text-center text-sm text-muted-foreground">Loading benchmark overrides...</div>
                ) : (
                  <BenchmarkTable
                    benchmarks={sortedBenchmarks}
                    subjects={subjects}
                    canManage={canManage}
                    deletingId={deletingId}
                    onEdit={(benchmark) => {
                      setSubmitError("");
                      setEditingBenchmark(benchmark);
                    }}
                    onDelete={(benchmark) => {
                      void handleDelete(benchmark);
                    }}
                  />
                )}
              </CardContent>
            </Card>
          </CardContent>
        </Card>

        <Dialog
          open={editingBenchmark !== null}
          onOpenChange={(open) => {
            if (!open) {
              setEditingBenchmark(null);
              setSubmitError("");
            }
          }}
        >
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Edit Benchmark Override</DialogTitle>
            </DialogHeader>
            <BenchmarkForm
              key={editingBenchmark?.id ?? "edit-empty"}
              mode="edit"
              subjects={subjects}
              initialValues={editInitialValues}
              error={submitError}
              submitting={isSubmitting}
              onSubmit={handleUpdate}
              onCancel={() => {
                setEditingBenchmark(null);
                setSubmitError("");
              }}
            />
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
