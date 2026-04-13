"use client";

import { useEffect, useState } from "react";

import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { ScoreType, Student, Subject } from "@/lib/types";

const SCORE_TYPES: ScoreType[] = ["homework", "quiz", "test"];

export default function ScoreEntryPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [form, setForm] = useState({
    student_id: "",
    subject_id: "",
    score_type: "quiz" as ScoreType,
    value: "",
    date: new Date().toISOString().slice(0, 10),
    notes: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [studentData, subjectData] = await Promise.all([
          api.get<Student[]>("/students"),
          api.get<Subject[]>("/lookups/subjects"),
        ]);
        setStudents(studentData);
        setSubjects(subjectData);
        setForm((current) => ({
          ...current,
          student_id: current.student_id || studentData[0]?.id || "",
          subject_id: current.subject_id || subjectData[0]?.id || "",
        }));
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load score entry form");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");
    try {
      await api.post("/scores", {
        student_id: form.student_id,
        subject_id: form.subject_id,
        score_type: form.score_type,
        value: Number(form.value),
        date: form.date,
        notes: form.notes || null,
      });
      setMessage("Score saved successfully.");
      setForm((current) => ({ ...current, value: "", notes: "" }));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to save score");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <Header title="Enter Scores" />
      <div className="p-6">
        <Card className="max-w-2xl">
          <CardContent className="p-6">
            {loading ? (
              <p className="text-sm text-slate-500">Loading score entry form...</p>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1">
                    <Label>Student</Label>
                    <Select value={form.student_id} onValueChange={(value) => setForm({ ...form, student_id: value ?? "" })}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select student">
                          {(value: string) => value ? (students.find((s) => s.id === value)?.name ?? value) : "Select student"}
                        </SelectValue>
                      </SelectTrigger>
                      <SelectContent>
                        {students.map((student) => (
                          <SelectItem key={student.id} value={student.id}>
                            {student.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label>Subject</Label>
                    <Select value={form.subject_id} onValueChange={(value) => setForm({ ...form, subject_id: value ?? "" })}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select subject">
                          {(value: string) => value ? (subjects.find((s) => s.id === value)?.name ?? value) : "Select subject"}
                        </SelectValue>
                      </SelectTrigger>
                      <SelectContent>
                        {subjects.map((subject) => (
                          <SelectItem key={subject.id} value={subject.id}>
                            {subject.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="space-y-1">
                    <Label>Score Type</Label>
                    <Select value={form.score_type} onValueChange={(value) => setForm({ ...form, score_type: (value ?? "quiz") as ScoreType })}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select score type" />
                      </SelectTrigger>
                      <SelectContent>
                        {SCORE_TYPES.map((scoreType) => (
                          <SelectItem key={scoreType} value={scoreType}>
                            {scoreType}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="score-value">Score</Label>
                    <Input
                      id="score-value"
                      type="number"
                      min={0}
                      max={100}
                      value={form.value}
                      onChange={(event) => setForm({ ...form, value: event.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="score-date">Date</Label>
                    <Input
                      id="score-date"
                      type="date"
                      value={form.date}
                      onChange={(event) => setForm({ ...form, date: event.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="score-notes">Notes</Label>
                  <Textarea
                    id="score-notes"
                    value={form.notes}
                    onChange={(event) => setForm({ ...form, notes: event.target.value })}
                    rows={4}
                  />
                </div>
                {message ? <p className="text-sm text-green-700">{message}</p> : null}
                {error ? <p className="text-sm text-red-600">{error}</p> : null}
                <Button type="submit" disabled={saving}>
                  {saving ? "Saving..." : "Save Score"}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
