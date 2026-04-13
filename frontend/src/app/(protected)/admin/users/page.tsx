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
import type { School, User, UserRole } from "@/lib/types";

const ROLES: UserRole[] = ["it_admin", "district_admin", "principal", "teacher"];

export default function UsersAdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [schools, setSchools] = useState<School[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ username: "", password: "", role: "", school_id: "" });
  const [error, setError] = useState("");

  async function load() {
    const [userData, schoolData] = await Promise.all([
      api.get<User[]>("/admin/users"),
      api.get<School[]>("/admin/schools"),
    ]);
    setUsers(userData);
    setSchools(schoolData);
  }

  useEffect(() => {
    async function loadData() {
      try {
        await load();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load users");
      }
    }

    void loadData();
  }, []);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api.post("/admin/users", {
        username: form.username,
        password: form.password,
        role: form.role,
        school_id: form.school_id || null,
      });
      setForm({ username: "", password: "", role: "", school_id: "" });
      setOpen(false);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to create user");
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this user?")) {
      return;
    }
    await api.delete(`/admin/users/${id}`);
    await load();
  }

  return (
    <div>
      <Header title="User Management" />
      <div className="space-y-4 p-6">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger render={<Button>Add User</Button>} />
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New User</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="new-username">Username</Label>
                <Input
                  id="new-username"
                  value={form.username}
                  onChange={(event) => setForm({ ...form, username: event.target.value })}
                  required
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="new-password">Password</Label>
                <Input
                  id="new-password"
                  type="password"
                  value={form.password}
                  onChange={(event) => setForm({ ...form, password: event.target.value })}
                  required
                />
              </div>
              <div className="space-y-1">
                <Label>Role</Label>
                <Select value={form.role} onValueChange={(value) => setForm({ ...form, role: value ?? "" })}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select role" />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLES.map((role) => (
                      <SelectItem key={role} value={role}>
                        {role}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>School</Label>
                <Select value={form.school_id} onValueChange={(value) => setForm({ ...form, school_id: value ?? "" })}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Optional school assignment">
                      {(value: string) => value ? (schools.find((s) => s.id === value)?.name ?? value) : "Optional school assignment"}
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
              {error ? <p className="text-sm text-red-600">{error}</p> : null}
              <Button type="submit" className="w-full">
                Create User
              </Button>
            </form>
          </DialogContent>
        </Dialog>

        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Username</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>School</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium">{user.username}</TableCell>
                    <TableCell>{user.role}</TableCell>
                    <TableCell>{schools.find((school) => school.id === user.school_id)?.name ?? "—"}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => void handleDelete(user.id)}>
                        Delete
                      </Button>
                    </TableCell>
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
