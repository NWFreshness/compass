"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Header } from "@/components/layout/header";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import type { Score, Student, Subject } from "@/lib/types";

export default function StudentDetailPage() {
  const params = useParams<{ id: string }>();
  const [student, setStudent] = useState<Student | null>(null);
  const [scores, setScores] = useState<Score[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [studentData, scoreData, subjectData] = await Promise.all([
          api.get<Student>(`/students/${params.id}`),
          api.get<Score[]>(`/scores/student/${params.id}`),
          api.get<Subject[]>("/lookups/subjects"),
        ]);
        setStudent(studentData);
        setScores(scoreData);
        setSubjects(subjectData);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load student profile");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [params.id]);

  const subjectNames = useMemo(
    () => Object.fromEntries(subjects.map((subject) => [subject.id, subject.name])),
    [subjects]
  );

  return (
    <div>
      <Header title={student ? student.name : "Student Profile"} />
      <div className="space-y-4 p-6">
        <Link href="/students" className={buttonVariants({ variant: "outline" })}>
          Back to Students
        </Link>

        {loading ? (
          <Card>
            <CardContent className="p-6 text-sm text-slate-500">Loading student profile...</CardContent>
          </Card>
        ) : error ? (
          <Card>
            <CardContent className="p-6 text-sm text-red-600">{error}</CardContent>
          </Card>
        ) : student ? (
          <>
            <Card>
              <CardContent className="grid gap-4 p-6 sm:grid-cols-3">
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
              </CardContent>
            </Card>

            <Card>
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
                          <TableCell>{score.date}</TableCell>
                          <TableCell>{subjectNames[score.subject_id] ?? score.subject_id}</TableCell>
                          <TableCell className="capitalize">{score.score_type}</TableCell>
                          <TableCell>{score.value}%</TableCell>
                          <TableCell>{score.notes || "—"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    </div>
  );
}
