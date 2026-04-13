"use client";

import { useEffect, useState } from "react";

import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import type { Subject } from "@/lib/types";

export default function SubjectsAdminPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setSubjects(await api.get<Subject[]>("/admin/subjects"));
  }

  useEffect(() => {
    async function loadData() {
      try {
        await load();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load subjects");
      }
    }

    void loadData();
  }, []);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api.post("/admin/subjects", { name });
      setName("");
      setOpen(false);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to create subject");
    }
  }

  return (
    <div>
      <Header title="Subjects" />
      <div className="space-y-4 p-6">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger render={<Button>Add Subject</Button>} />
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New Subject</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="subject-name">Subject Name</Label>
                <Input
                  id="subject-name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  required
                />
              </div>
              {error ? <p className="text-sm text-red-600">{error}</p> : null}
              <Button type="submit" className="w-full">
                Create Subject
              </Button>
            </form>
          </DialogContent>
        </Dialog>

        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Subject</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {subjects.map((subject) => (
                  <TableRow key={subject.id}>
                    <TableCell className="font-medium">{subject.name}</TableCell>
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
