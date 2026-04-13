"use client";

import { useEffect, useMemo, useState } from "react";

import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { InterventionForm } from "@/components/interventions/InterventionForm";
import { InterventionList } from "@/components/interventions/InterventionList";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import type { Intervention } from "@/lib/types";

interface ClassInterventionPanelProps {
  classId: string;
  className: string;
  gradeLevel: number;
  compact?: boolean;
}

function sortInterventions(items: Intervention[]) {
  return [...items].sort((a, b) => {
    if (a.status !== b.status) {
      return a.status.localeCompare(b.status);
    }
    return b.start_date.localeCompare(a.start_date);
  });
}

export function ClassInterventionPanel({
  classId,
  className,
  gradeLevel,
  compact = false,
}: ClassInterventionPanelProps) {
  const { user, loading: authLoading } = useAuth();
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const result = await api.get<Intervention[]>(`/interventions?class_id=${classId}`);
        setInterventions(sortInterventions(result));
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load interventions");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [classId]);

  const activeCount = useMemo(
    () => interventions.filter((intervention) => intervention.status === "active").length,
    [interventions]
  );

  function handleCreated(intervention: Intervention) {
    setInterventions((current) => sortInterventions([intervention, ...current]));
    setShowForm(false);
  }

  function handleUpdated(updated: Intervention) {
    setInterventions((current) =>
      sortInterventions(current.map((intervention) => (intervention.id === updated.id ? updated : intervention)))
    );
  }

  return (
    <Card className={compact ? "border-dashed" : undefined}>
      <CardHeader className="pb-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle className="text-base">Class Interventions</CardTitle>
            <p className="text-sm text-slate-500">
              {className} · Grade {gradeLevel}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {activeCount > 0 ? `${activeCount} active intervention${activeCount === 1 ? "" : "s"}` : "No active interventions"}
            </p>
          </div>
          {!authLoading && user ? (
            <button
              type="button"
              className={buttonVariants({ variant: showForm ? "outline" : "default" })}
              onClick={() => setShowForm((current) => !current)}
            >
              {showForm ? "Cancel" : "Add Class Intervention"}
            </button>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {showForm && user ? (
          <div className="rounded-lg border border-slate-200 p-4">
            <InterventionForm
              target={{ type: "class", id: classId }}
              onCreated={handleCreated}
              onCancel={() => setShowForm(false)}
            />
          </div>
        ) : null}

        {loading ? (
          <p className="text-sm text-slate-500">Loading interventions...</p>
        ) : error ? (
          <p className="text-sm text-red-600">{error}</p>
        ) : user ? (
          <InterventionList
            interventions={interventions}
            userRole={user.role}
            onUpdated={handleUpdated}
          />
        ) : (
          <p className="text-sm text-slate-500">Loading intervention permissions...</p>
        )}
      </CardContent>
    </Card>
  );
}
