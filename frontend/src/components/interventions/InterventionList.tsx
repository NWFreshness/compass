"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Intervention, UserRole } from "@/lib/types";
import { InterventionStatusBadge } from "./InterventionStatusBadge";

interface Props {
  interventions: Intervention[];
  userRole: UserRole;
  onUpdated: (updated: Intervention) => void;
}

function canEdit(role: UserRole) {
  return role !== "district_admin";
}

export function InterventionList({ interventions, userRole, onUpdated }: Props) {
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [outcomeNotes, setOutcomeNotes] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  const active = interventions.filter((iv) => iv.status === "active");
  const resolved = interventions.filter((iv) => iv.status === "resolved");

  async function resolve(iv: Intervention) {
    setResolvingId(iv.id);
    setError("");
    try {
      const notes = outcomeNotes[iv.id] ?? "";
      const updated = await api.patch<Intervention>(`/interventions/${iv.id}`, {
        status: "resolved",
        outcome_notes: notes || null,
      });
      onUpdated(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to update intervention");
    } finally {
      setResolvingId(null);
    }
  }

  if (interventions.length === 0) {
    return <p className="text-sm text-slate-500">No interventions recorded.</p>;
  }

  return (
    <div className="space-y-4">
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      {active.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Active</p>
          {active.map((iv) => (
            <InterventionRow
              key={iv.id}
              iv={iv}
              editable={canEdit(userRole)}
              resolvingId={resolvingId}
              outcomeNote={outcomeNotes[iv.id] ?? ""}
              onNoteChange={(val) => setOutcomeNotes({ ...outcomeNotes, [iv.id]: val })}
              onResolve={() => void resolve(iv)}
            />
          ))}
        </div>
      )}

      {resolved.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Resolved</p>
          {resolved.map((iv) => (
            <InterventionRow key={iv.id} iv={iv} editable={false} resolvingId={null} outcomeNote="" onNoteChange={() => undefined} onResolve={() => undefined} />
          ))}
        </div>
      )}
    </div>
  );
}

function InterventionRow({
  iv,
  editable,
  resolvingId,
  outcomeNote,
  onNoteChange,
  onResolve,
}: {
  iv: Intervention;
  editable: boolean;
  resolvingId: string | null;
  outcomeNote: string;
  onNoteChange: (val: string) => void;
  onResolve: () => void;
}) {
  return (
    <div className="rounded border border-slate-200 p-3 text-sm space-y-1">
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium">{iv.strategy}</span>
        <InterventionStatusBadge status={iv.status} />
      </div>
      {iv.description ? <p className="text-slate-600">{iv.description}</p> : null}
      <p className="text-xs text-slate-400">Started {iv.start_date}</p>
      {iv.outcome_notes ? <p className="text-slate-600 text-xs">Outcome: {iv.outcome_notes}</p> : null}
      {editable && iv.status === "active" && (
        <div className="pt-1 space-y-1">
          <input
            className="w-full rounded border border-slate-200 px-2 py-1 text-xs"
            placeholder="Outcome notes (optional)"
            value={outcomeNote}
            onChange={(e) => onNoteChange(e.target.value)}
          />
          <Button
            size="sm"
            variant="outline"
            disabled={resolvingId === iv.id}
            onClick={onResolve}
          >
            {resolvingId === iv.id ? "Resolving..." : "Mark Resolved"}
          </Button>
        </div>
      )}
    </div>
  );
}
