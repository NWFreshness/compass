"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { BenchmarkFormValues, Subject } from "@/lib/types";

const GRADE_OPTIONS = Array.from({ length: 12 }, (_, index) => String(index + 1));

export interface BenchmarkSubmitPayload {
  grade_level: number;
  subject_id: string;
  tier1_min: number;
  tier2_min: number;
}

interface BenchmarkFormProps {
  mode: "create" | "edit";
  subjects: Subject[];
  initialValues: BenchmarkFormValues;
  error?: string;
  submitting?: boolean;
  onSubmit: (payload: BenchmarkSubmitPayload) => Promise<void> | void;
  onCancel?: () => void;
}

export function BenchmarkForm({
  mode,
  subjects,
  initialValues,
  error = "",
  submitting = false,
  onSubmit,
  onCancel,
}: BenchmarkFormProps) {
  const [values, setValues] = useState<BenchmarkFormValues>(initialValues);
  const [validationError, setValidationError] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError("");

    const tier1Min = Number(values.tier1_min);
    const tier2Min = Number(values.tier2_min);
    const gradeLevel = Number(values.grade_level);

    if (!values.grade_level || !values.subject_id) {
      setValidationError("Grade and subject are required.");
      return;
    }

    if ([tier1Min, tier2Min, gradeLevel].some((value) => Number.isNaN(value))) {
      setValidationError("Enter valid numeric thresholds.");
      return;
    }

    if (tier1Min < tier2Min) {
      setValidationError("Tier 1 minimum must be greater than or equal to Tier 2 minimum.");
      return;
    }

    await onSubmit({
      grade_level: gradeLevel,
      subject_id: values.subject_id,
      tier1_min: tier1Min,
      tier2_min: tier2Min,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1">
          <Label>Grade</Label>
          <Select
            value={values.grade_level}
            onValueChange={(value) => setValues((current) => ({ ...current, grade_level: value ?? "" }))}
            disabled={mode === "edit" || submitting}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select grade" />
            </SelectTrigger>
            <SelectContent>
              {GRADE_OPTIONS.map((grade) => (
                <SelectItem key={grade} value={grade}>
                  Grade {grade}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1">
          <Label>Subject</Label>
          <Select
            value={values.subject_id}
            onValueChange={(value) => setValues((current) => ({ ...current, subject_id: value ?? "" }))}
            disabled={mode === "edit" || submitting}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select subject">
                {(value: string) => value ? (subjects.find((subject) => subject.id === value)?.name ?? value) : "Select subject"}
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

      {mode === "edit" ? (
        <p className="text-sm text-muted-foreground">
          Grade and subject stay fixed for an override. Delete and recreate the row if you need a different pairing.
        </p>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1">
          <Label htmlFor="benchmark-tier1">Tier 1 Minimum</Label>
          <Input
            id="benchmark-tier1"
            type="number"
            min={0}
            max={100}
            step="0.1"
            value={values.tier1_min}
            onChange={(event) => {
              setValidationError("");
              setValues((current) => ({ ...current, tier1_min: event.target.value }));
            }}
            required
            disabled={submitting}
          />
        </div>

        <div className="space-y-1">
          <Label htmlFor="benchmark-tier2">Tier 2 Minimum</Label>
          <Input
            id="benchmark-tier2"
            type="number"
            min={0}
            max={100}
            step="0.1"
            value={values.tier2_min}
            onChange={(event) => {
              setValidationError("");
              setValues((current) => ({ ...current, tier2_min: event.target.value }));
            }}
            required
            disabled={submitting}
          />
        </div>
      </div>

      {validationError ? <p className="text-sm text-red-600">{validationError}</p> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <div className="flex justify-end gap-2">
        {onCancel ? (
          <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
            Cancel
          </Button>
        ) : null}
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : mode === "create" ? "Create Override" : "Save Changes"}
        </Button>
      </div>
    </form>
  );
}
