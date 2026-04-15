"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import type { Class, School, Student } from "@/lib/types";

type ReportType = "student" | "class" | "school" | "district";
type ReportFormat = "csv" | "pdf";

async function triggerDownload(path: string, filename: string) {
  const res = await fetch(`/api${path}`, { credentials: "include" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function ReportsPage() {
  const { user } = useAuth();
  const [reportType, setReportType] = useState<ReportType>("student");
  const [format, setFormat] = useState<ReportFormat>("csv");
  const [students, setStudents] = useState<Student[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  const [schools, setSchools] = useState<School[]>([]);
  const [selectedStudent, setSelectedStudent] = useState("");
  const [selectedClass, setSelectedClass] = useState("");
  const [selectedSchool, setSelectedSchool] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [s, c, sc] = await Promise.all([
          api.get<Student[]>("/students"),
          api.get<Class[]>("/lookups/classes"),
          api.get<School[]>("/lookups/schools"),
        ]);
        setStudents(s);
        setClasses(c);
        setSchools(sc);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load report filters");
      }
    }
    void load();
  }, []);

  const canDistrict = user?.role === "it_admin" || user?.role === "district_admin";
  const canSchool = canDistrict || user?.role === "principal";

  const availableTypes: { value: ReportType; label: string }[] = [
    { value: "student", label: "Student Report" },
    { value: "class", label: "Class Report" },
    ...(canSchool ? [{ value: "school" as ReportType, label: "School Report" }] : []),
    ...(canDistrict ? [{ value: "district" as ReportType, label: "District Report" }] : []),
  ];

  async function handleDownload() {
    setError("");
    setDownloading(true);
    try {
      let path = "";
      let filename = "";
      if (reportType === "student" && selectedStudent) {
        path = `/reports/student/${selectedStudent}?format=${format}`;
        filename = `student_report.${format}`;
      } else if (reportType === "class" && selectedClass) {
        path = `/reports/class/${selectedClass}?format=${format}`;
        filename = `class_report.${format}`;
      } else if (reportType === "school" && selectedSchool) {
        path = `/reports/school/${selectedSchool}?format=${format}`;
        filename = `school_report.${format}`;
      } else if (reportType === "district") {
        path = `/reports/district?format=${format}`;
        filename = `district_report.${format}`;
      }
      if (!path) {
        setError("Please select a target.");
        return;
      }
      await triggerDownload(path, filename);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div>
      <Header title="Reports" />
      <div className="space-y-4 p-6 max-w-lg">
        <Card>
          <CardContent className="space-y-4 p-6">
            <div className="space-y-1">
              <label className="text-sm font-medium">Report Type</label>
              <Select value={reportType} onValueChange={(v) => { if (v) setReportType(v as ReportType); }}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {availableTypes.map((t) => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {reportType === "student" && (
              <div className="space-y-1">
                <label className="text-sm font-medium">Student</label>
                <Select value={selectedStudent} onValueChange={(v) => { if (v) setSelectedStudent(v); }}>
                  <SelectTrigger>
                    <span className={!selectedStudent ? "text-muted-foreground" : ""}>
                      {selectedStudent ? (students.find((s) => s.id === selectedStudent)?.name ?? "Select student") : "Select student"}
                    </span>
                  </SelectTrigger>
                  <SelectContent>
                    {students.map((s) => (
                      <SelectItem key={s.id} value={s.id}>{s.name} ({s.student_id_number})</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {reportType === "class" && (
              <div className="space-y-1">
                <label className="text-sm font-medium">Class</label>
                <Select value={selectedClass} onValueChange={(v) => { if (v) setSelectedClass(v); }}>
                  <SelectTrigger>
                    <span className={!selectedClass ? "text-muted-foreground" : ""}>
                      {selectedClass ? (classes.find((c) => c.id === selectedClass)?.name ?? "Select class") : "Select class"}
                    </span>
                  </SelectTrigger>
                  <SelectContent>
                    {classes.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.name} (Grade {c.grade_level})</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {reportType === "school" && (
              <div className="space-y-1">
                <label className="text-sm font-medium">School</label>
                <Select value={selectedSchool} onValueChange={(v) => { if (v) setSelectedSchool(v); }}>
                  <SelectTrigger>
                    <span className={!selectedSchool ? "text-muted-foreground" : ""}>
                      {selectedSchool ? (schools.find((s) => s.id === selectedSchool)?.name ?? "Select school") : "Select school"}
                    </span>
                  </SelectTrigger>
                  <SelectContent>
                    {schools.map((s) => (
                      <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-sm font-medium">Format</label>
              <Select value={format} onValueChange={(v) => { if (v) setFormat(v as ReportFormat); }}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="csv">CSV</SelectItem>
                  <SelectItem value="pdf">PDF</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button onClick={() => void handleDownload()} disabled={downloading} className="w-full">
              {downloading ? "Downloading..." : "Download Report"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
