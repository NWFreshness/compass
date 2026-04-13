"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Intervention } from "@/lib/types";

type Target =
  | { type: "student"; id: string }
  | { type: "class"; id: string };

interface Props {
  target: Target;
  onCreated: (intervention: Intervention) => void;
  onCancel: () => void;
}

export function InterventionForm({ target, onCreated, onCancel }: Props) {
  const [form, setForm] = useState({
    strategy: "",
    description: "",
    start_date: new Date().toISOString().slice(0, 10),
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const body = {
        strategy: form.strategy,
        description: form.description || null,
        start_date: form.start_date,
        student_id: target.type === "student" ? target.id : null,
        class_id: target.type === "class" ? target.id : null,
      };
      const intervention = await api.post<Intervention>("/interventions", body);
      onCreated(intervention);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to save intervention");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="space-y-1">
        <Label htmlFor="iv-strategy">Strategy</Label>
        <Input
          id="iv-strategy"
          value={form.strategy}
          onChange={(e) => setForm({ ...form, strategy: e.target.value })}
          required
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="iv-description">Description</Label>
        <Textarea
          id="iv-description"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          rows={3}
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="iv-start-date">Start Date</Label>
        <Input
          id="iv-start-date"
          type="date"
          value={form.start_date}
          onChange={(e) => setForm({ ...form, start_date: e.target.value })}
          required
        />
      </div>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <div className="flex gap-2">
        <Button type="submit" disabled={saving}>
          {saving ? "Saving..." : "Add Intervention"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
