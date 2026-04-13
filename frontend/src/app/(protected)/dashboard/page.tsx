"use client";

import { useEffect, useState } from "react";

import { DistrictDashboard } from "@/components/dashboard/DistrictDashboard";
import { PrincipalDashboard } from "@/components/dashboard/PrincipalDashboard";
import { TeacherDashboard } from "@/components/dashboard/TeacherDashboard";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { DistrictDashboard as DistrictDashboardData, PrincipalDashboard as PrincipalDashboardData, TeacherDashboard as TeacherDashboardData } from "@/lib/types";

type DashboardData = TeacherDashboardData | PrincipalDashboardData | DistrictDashboardData;
type DashboardConfig = {
  endpoint: string;
  render: (data: DashboardData) => React.ReactNode;
};

const DASHBOARD_CONFIG: Record<string, DashboardConfig> = {
  teacher: {
    endpoint: "/dashboard/teacher",
    render: (data) => <TeacherDashboard data={data as TeacherDashboardData} />,
  },
  principal: {
    endpoint: "/dashboard/principal",
    render: (data) => <PrincipalDashboard data={data as PrincipalDashboardData} />,
  },
  district_admin: {
    endpoint: "/dashboard/district",
    render: (data) => <DistrictDashboard data={data as DistrictDashboardData} />,
  },
  it_admin: {
    endpoint: "/dashboard/district",
    render: (data) => <DistrictDashboard data={data as DistrictDashboardData} />,
  },
};

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!user) {
      setLoading(false);
      return;
    }

    const config = DASHBOARD_CONFIG[user.role];
    if (!config) {
      setError("Unsupported dashboard role");
      setLoading(false);
      return;
    }

    async function load() {
      setLoading(true);
      setError("");
      try {
        const result = await api.get<DashboardData>(config.endpoint);
        setData(result);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load dashboard");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [authLoading, user]);

  function renderDashboard() {
    if (authLoading || loading) {
      return <div className="p-6 text-sm text-slate-500">Loading dashboard...</div>;
    }
    if (error) {
      return <div className="p-6 text-sm text-red-600">{error}</div>;
    }
    if (!data || !user) return null;

    return DASHBOARD_CONFIG[user.role]?.render(data) ?? null;
  }

  return (
    <div>
      <Header title="Dashboard" />
      {renderDashboard()}
    </div>
  );
}
