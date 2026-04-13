"use client";

import { useEffect, useState } from "react";

import { PrincipalDashboard } from "@/components/dashboard/PrincipalDashboard";
import { TeacherDashboard } from "@/components/dashboard/TeacherDashboard";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Class } from "@/lib/types";

export default function DashboardPage() {
  const { user } = useAuth();
  const [classes, setClasses] = useState<Class[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await api.get<Class[]>("/lookups/classes");
        setClasses(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load dashboard");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const isTeacher = user?.role === "teacher" || user?.role === "it_admin";
  const isPrincipal = user?.role === "principal" || user?.role === "district_admin";

  return (
    <div>
      <Header title="Dashboard" />
      <div className="space-y-4 p-6">
        {loading ? (
          <Card>
            <CardContent className="p-6 text-sm text-slate-500">Loading dashboard...</CardContent>
          </Card>
        ) : error ? (
          <Card>
            <CardContent className="p-6 text-sm text-red-600">{error}</CardContent>
          </Card>
        ) : isTeacher ? (
          <TeacherDashboard classes={classes} />
        ) : isPrincipal ? (
          <PrincipalDashboard classes={classes} />
        ) : (
          <Card>
            <CardContent className="p-6 text-sm text-slate-500">
              Dashboard is not available for your role.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
