"use client";

import { useEffect, useState } from "react";

import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import type { Class, School, User } from "@/lib/types";

export default function ClassesAdminPage() {
  const [classes, setClasses] = useState<Class[]>([]);
  const [schools, setSchools] = useState<School[]>([]);
  const [teachers, setTeachers] = useState<User[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", grade_level: "", school_id: "", teacher_id: "" });
  const [error, setError] = useState("");

  async function load() {
    const [classData, schoolData, userData] = await Promise.all([
      api.get<Class[]>("/admin/classes"),
      api.get<School[]>("/admin/schools"),
      api.get<User[]>("/admin/users"),
    ]);
    setClasses(classData);
    setSchools(schoolData);
    setTeachers(userData.filter((user) => user.role === "teacher"));
  }

  useEffect(() => {
    async function loadData() {
      try {
        await load();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load classes");
      }
    }

    void loadData();
  }, []);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api.post("/admin/classes", {
        name: form.name,
        grade_level: Number(form.grade_level),
        school_id: form.school_id,
        teacher_id: form.teacher_id || null,
      });
      setForm({ name: "", grade_level: "", school_id: "", teacher_id: "" });
      setOpen(false);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to create class");
    }
  }

  return (
    <div>
      <Header title="Classes" />
      <div className="space-y-4 p-6">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger render={<Button>Add Class</Button>} />
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New Class</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="class-name">Class Name</Label>
                <Input
                  id="class-name"
                  value={form.name}
                  onChange={(event) => setForm({ ...form, name: event.target.value })}
                  required
                />
              </div>
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
                    <SelectValue placeholder="Select school">
                      {(value: string) => value ? (schools.find((s) => s.id === value)?.name ?? value) : "Select school"}
                    </SelectValue>
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
              <div className="space-y-1">
                <Label>Teacher</Label>
                <Select value={form.teacher_id} onValueChange={(value) => setForm({ ...form, teacher_id: value ?? "" })}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Optional teacher assignment">
                      {(value: string) => value ? (teachers.find((t) => t.id === value)?.username ?? value) : "Optional teacher assignment"}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {teachers.map((teacher) => (
                      <SelectItem key={teacher.id} value={teacher.id}>
                        {teacher.username}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {error ? <p className="text-sm text-red-600">{error}</p> : null}
              <Button type="submit" className="w-full">
                Create Class
              </Button>
            </form>
          </DialogContent>
        </Dialog>

        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Grade</TableHead>
                  <TableHead>School</TableHead>
                  <TableHead>Teacher</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {classes.map((klass) => (
                  <TableRow key={klass.id}>
                    <TableCell className="font-medium">{klass.name}</TableCell>
                    <TableCell>Grade {klass.grade_level}</TableCell>
                    <TableCell>{schools.find((school) => school.id === klass.school_id)?.name ?? klass.school_id}</TableCell>
                    <TableCell>{teachers.find((teacher) => teacher.id === klass.teacher_id)?.username ?? "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
