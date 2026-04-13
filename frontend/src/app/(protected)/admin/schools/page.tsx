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
import type { School } from "@/lib/types";

export default function SchoolsAdminPage() {
  const [schools, setSchools] = useState<School[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", address: "" });
  const [error, setError] = useState("");

  async function load() {
    setSchools(await api.get<School[]>("/admin/schools"));
  }

  useEffect(() => {
    async function loadData() {
      try {
        await load();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load schools");
      }
    }

    void loadData();
  }, []);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api.post("/admin/schools", form);
      setForm({ name: "", address: "" });
      setOpen(false);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to create school");
    }
  }

  return (
    <div>
      <Header title="Schools" />
      <div className="space-y-4 p-6">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger render={<Button>Add School</Button>} />
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New School</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="school-name">School Name</Label>
                <Input
                  id="school-name"
                  value={form.name}
                  onChange={(event) => setForm({ ...form, name: event.target.value })}
                  required
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="school-address">Address</Label>
                <Input
                  id="school-address"
                  value={form.address}
                  onChange={(event) => setForm({ ...form, address: event.target.value })}
                />
              </div>
              {error ? <p className="text-sm text-red-600">{error}</p> : null}
              <Button type="submit" className="w-full">
                Create School
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
                  <TableHead>Address</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {schools.map((school) => (
                  <TableRow key={school.id}>
                    <TableCell className="font-medium">{school.name}</TableCell>
                    <TableCell>{school.address || "—"}</TableCell>
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
