"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Header } from "@/components/layout/header";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Class, School, Student } from "@/lib/types";

export default function StudentsPage() {
  const { user } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [schools, setSchools] = useState<School[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [studentData, schoolData, classData] = await Promise.all([
          api.get<Student[]>("/students"),
          api.get<School[]>("/lookups/schools"),
          api.get<Class[]>("/lookups/classes"),
        ]);
        setStudents(studentData);
        setSchools(schoolData);
        setClasses(classData);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load students");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const schoolNames = useMemo(
    () => Object.fromEntries(schools.map((school) => [school.id, school.name])),
    [schools]
  );
  const classNames = useMemo(
    () => Object.fromEntries(classes.map((klass) => [klass.id, klass.name])),
    [classes]
  );

  const filteredStudents = students.filter((student) => {
    const term = search.trim().toLowerCase();
    if (!term) {
      return true;
    }
    return student.name.toLowerCase().includes(term) || student.student_id_number.toLowerCase().includes(term);
  });

  return (
    <div>
      <Header title="Students" />
      <div className="space-y-4 p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by student name or ID"
            className="sm:max-w-sm"
          />
          {user && user.role !== "district_admin" ? (
            <Link href="/students/new" className={buttonVariants({ variant: "default" })}>
              Add Student
            </Link>
          ) : null}
        </div>

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 text-sm text-slate-500">Loading students...</div>
            ) : error ? (
              <div className="p-6 text-sm text-red-600">{error}</div>
            ) : filteredStudents.length === 0 ? (
              <div className="p-6 text-sm text-slate-500">No students found.</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Student</TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead>Grade</TableHead>
                    <TableHead>School</TableHead>
                    <TableHead>Class</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredStudents.map((student) => (
                    <TableRow key={student.id}>
                      <TableCell className="font-medium">
                        <Link href={`/students/${student.id}`} className="hover:underline">
                          {student.name}
                        </Link>
                      </TableCell>
                      <TableCell>{student.student_id_number}</TableCell>
                      <TableCell>Grade {student.grade_level}</TableCell>
                      <TableCell>{schoolNames[student.school_id] ?? student.school_id}</TableCell>
                      <TableCell>{student.class_id ? (classNames[student.class_id] ?? student.class_id) : "Unassigned"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
