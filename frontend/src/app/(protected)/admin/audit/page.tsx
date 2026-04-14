"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import type { AuditLogPage } from "@/lib/types";

const PER_PAGE = 50;

export default function AuditLogPage() {
  const [data, setData] = useState<AuditLogPage | null>(null);
  const [page, setPage] = useState(1);
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = new URLSearchParams({ page: String(page), per_page: String(PER_PAGE) });
        if (action) params.set("action", action);
        if (entityType) params.set("entity_type", entityType);
        const result = await api.get<AuditLogPage>(`/audit?${params.toString()}`);
        setData(result);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load audit log");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [page, action, entityType]);

  const totalPages = data ? Math.ceil(data.total / PER_PAGE) : 1;

  function formatTs(ts: string) {
    return new Date(ts).toLocaleString();
  }

  return (
    <div>
      <Header title="Audit Log" />
      <div className="space-y-4 p-6">
        <div className="flex flex-wrap gap-3">
          <Input
            value={action}
            onChange={(e) => { setAction(e.target.value); setPage(1); }}
            placeholder="Filter by action (e.g. login)"
            className="w-48"
          />
          <Input
            value={entityType}
            onChange={(e) => { setEntityType(e.target.value); setPage(1); }}
            placeholder="Filter by entity type"
            className="w-48"
          />
          {data && (
            <span className="self-center text-sm text-slate-500">{data.total} total entries</span>
          )}
        </div>

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 text-sm text-slate-500">Loading audit log...</div>
            ) : error ? (
              <div className="p-6 text-sm text-red-600">{error}</div>
            ) : !data || data.entries.length === 0 ? (
              <div className="p-6 text-sm text-slate-500">No audit entries found.</div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Entity Type</TableHead>
                      <TableHead>Entity ID</TableHead>
                      <TableHead>Detail</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.entries.map((entry) => (
                      <TableRow key={entry.id}>
                        <TableCell className="whitespace-nowrap text-xs text-slate-500">{formatTs(entry.timestamp)}</TableCell>
                        <TableCell>
                          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-mono text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                            {entry.action}
                          </span>
                        </TableCell>
                        <TableCell className="text-sm">{entry.entity_type}</TableCell>
                        <TableCell className="font-mono text-xs text-slate-400">{entry.entity_id ? entry.entity_id.slice(0, 8) + "\u2026" : "\u2014"}</TableCell>
                        <TableCell className="max-w-xs truncate text-sm text-slate-600">{entry.detail || "\u2014"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="rounded border px-3 py-1 text-sm disabled:opacity-40"
              onClick={() => setPage((p) => p - 1)}
              disabled={page <= 1}
            >
              Previous
            </button>
            <span className="text-sm text-slate-500">Page {page} of {totalPages}</span>
            <button
              type="button"
              className="rounded border px-3 py-1 text-sm disabled:opacity-40"
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= totalPages}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
