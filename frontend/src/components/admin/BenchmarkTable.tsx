"use client";

import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Benchmark, Subject } from "@/lib/types";

interface BenchmarkTableProps {
  benchmarks: Benchmark[];
  subjects: Subject[];
  canManage: boolean;
  deletingId?: string | null;
  onEdit: (benchmark: Benchmark) => void;
  onDelete: (benchmark: Benchmark) => void;
}

function formatThreshold(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

export function BenchmarkTable({
  benchmarks,
  subjects,
  canManage,
  deletingId = null,
  onEdit,
  onDelete,
}: BenchmarkTableProps) {
  if (!benchmarks.length) {
    return (
      <div className="px-4 py-8 text-center text-sm text-muted-foreground">
        No benchmark overrides match the current filters. The system will use the default thresholds instead.
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Grade</TableHead>
          <TableHead>Subject</TableHead>
          <TableHead>Tier 1 Minimum</TableHead>
          <TableHead>Tier 2 Minimum</TableHead>
          {canManage ? <TableHead className="text-right">Actions</TableHead> : null}
        </TableRow>
      </TableHeader>
      <TableBody>
        {benchmarks.map((benchmark) => (
          <TableRow key={benchmark.id}>
            <TableCell className="font-medium">Grade {benchmark.grade_level}</TableCell>
            <TableCell>{subjects.find((subject) => subject.id === benchmark.subject_id)?.name ?? benchmark.subject_id}</TableCell>
            <TableCell>{formatThreshold(benchmark.tier1_min)}</TableCell>
            <TableCell>{formatThreshold(benchmark.tier2_min)}</TableCell>
            {canManage ? (
              <TableCell className="text-right">
                <div className="flex justify-end gap-2">
                  <Button variant="outline" size="sm" onClick={() => onEdit(benchmark)}>
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(benchmark)}
                    disabled={deletingId === benchmark.id}
                  >
                    {deletingId === benchmark.id ? "Deleting..." : "Delete"}
                  </Button>
                </div>
              </TableCell>
            ) : null}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
