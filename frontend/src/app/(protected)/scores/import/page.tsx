"use client";

import { useState } from "react";

import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import type { CSVImportResult } from "@/lib/types";

export default function ScoreImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<CSVImportResult | null>(null);

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }

    setUploading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      setResult(await api.upload<CSVImportResult>("/scores/import", formData));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to import scores");
    } finally {
      setUploading(false);
    }
  }

  function downloadTemplate() {
    window.location.href = "/api/scores/template.csv";
  }

  return (
    <div>
      <Header title="Import Scores" />
      <div className="space-y-4 p-6">
        <Card className="max-w-2xl">
          <CardContent className="space-y-4 p-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="font-medium">Bulk score upload</p>
                <p className="text-sm text-slate-500">Upload a CSV using the Compass template.</p>
              </div>
              <Button type="button" variant="outline" onClick={downloadTemplate}>
                Download Template
              </Button>
            </div>

            <form onSubmit={handleUpload} className="space-y-4">
              <Input
                type="file"
                accept=".csv,text/csv"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
              {error ? <p className="text-sm text-red-600">{error}</p> : null}
              <Button type="submit" disabled={uploading}>
                {uploading ? "Importing..." : "Import Scores"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {result ? (
          <Card>
            <CardContent className="space-y-4 p-6">
              <div className="text-sm">
                <p className="font-medium">Import complete</p>
                <p className="text-slate-600">Imported rows: {result.imported}</p>
              </div>
              {result.errors.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Row</TableHead>
                      <TableHead>Message</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.errors.map((rowError) => (
                      <TableRow key={`${rowError.row}-${rowError.message}`}>
                        <TableCell>{rowError.row}</TableCell>
                        <TableCell>{rowError.message}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-sm text-green-700">No validation errors were reported.</p>
              )}
            </CardContent>
          </Card>
        ) : null}
      </div>
    </div>
  );
}
