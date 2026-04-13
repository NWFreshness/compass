"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Header } from "@/components/layout/header";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Class, School } from "@/lib/types";

type StudentForm = {
  name: string;
  student_id_number: string;
  grade_level: string;
  school_id: string;
  class_id: string;
};

const EMPTY_FORM: StudentForm = {
  name: "",
  student_id_number: "",
  grade_level: "",
  school_id: "",
  class_id: "",
};

export default function NewStudentPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [schools, setSchools] = useState<School[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  const [form, setForm] = useState<StudentForm>(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [schoolData, classData] = await Promise.all([
          api.get<School[]>("/lookups/schools"),
          api.get<Class[]>("/lookups/classes"),
        ]);
        setSchools(schoolData);
        setClasses(classData);
        setForm((current) => ({
          ...current,
          school_id: current.school_id || schoolData[0]?.id || "",
        }));
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load form options");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  useEffect(() => {
    if (!form.school_id) {
      return;
    }
    const availableClasses = classes.filter((klass) => klass.school_id === form.school_id);
    if (!availableClasses.some((klass) => klass.id === form.class_id)) {
      setForm((current) => ({ ...current, class_id: availableClasses[0]?.id || "" }));
    }
  }, [classes, form.class_id, form.school_id]);

  const availableClasses = classes.filter((klass) => !form.school_id || klass.school_id === form.school_id);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const student = await api.post<{ id: string }>("/students", {
        name: form.name,
        student_id_number: form.student_id_number,
        grade_level: Number(form.grade_level),
        school_id: form.school_id,
        class_id: form.class_id || null,
      });
      router.push(`/students/${student.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to create student");
    } finally {
      setSaving(false);
    }
  }

  if (user?.role === "district_admin") {
    return (
      <div>
        <Header title="New Student" />
        <div className="p-6 text-sm text-slate-500">District admins can view students but cannot create them.</div>
      </div>
    );
  }

  return (
    <div>
      <Header title="New Student" />
      <div className="p-6">
        <Card className="max-w-2xl">
          <CardContent className="p-6">
            {loading ? (
              <p className="text-sm text-slate-500">Loading form options...</p>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1">
                  <Label htmlFor="student-name">Student Name</Label>
                  <Input
                    id="student-name"
                    value={form.name}
                    onChange={(event) => setForm({ ...form, name: event.target.value })}
                    required
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="student-id">Student ID</Label>
                  <Input
                    id="student-id"
                    value={form.student_id_number}
                    onChange={(event) => setForm({ ...form, student_id_number: event.target.value })}
                    required
                  />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1">
                    <Label htmlFor="grade-level">Grade Level</Label>
                    <Input
                      id="grade-level"
                      type="number"
                      min={1}
                      max={12}
                      value={form.grade_level}
                      onChange={(event) => setForm({ ...form, grade_level: event.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>School</Label>
                    <Select value={form.school_id} onValueChange={(value) => setForm({ ...form, school_id: value ?? "" })}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select school" />
                      </SelectTrigger>
                      <SelectContent>
                        {schools.map((school) => (
                          <SelectItem key={school.id} value={school.id}>
                            {school.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-1">
                  <Label>Class</Label>
                  <Select value={form.class_id} onValueChange={(value) => setForm({ ...form, class_id: value ?? "" })}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select class" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableClasses.map((klass) => (
                        <SelectItem key={klass.id} value={klass.id}>
                          {klass.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {error ? <p className="text-sm text-red-600">{error}</p> : null}
                <div className="flex gap-3">
                  <Button type="submit" disabled={saving}>
                    {saving ? "Saving..." : "Create Student"}
                  </Button>
                  <Link href="/students" className={buttonVariants({ variant: "outline" })}>
                    Cancel
                  </Link>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
