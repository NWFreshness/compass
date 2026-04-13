export type UserRole = "it_admin" | "district_admin" | "principal" | "teacher";

export interface User {
  id: string;
  username: string;
  role: UserRole;
  school_id: string | null;
}

export interface School {
  id: string;
  name: string;
  address: string | null;
}

export interface Class {
  id: string;
  name: string;
  grade_level: number;
  school_id: string;
  teacher_id: string | null;
}

export interface Subject {
  id: string;
  name: string;
}

export interface Student {
  id: string;
  name: string;
  student_id_number: string;
  grade_level: number;
  school_id: string;
  class_id: string | null;
}

export type ScoreType = "homework" | "quiz" | "test";

export interface Score {
  id: string;
  student_id: string;
  subject_id: string;
  score_type: ScoreType;
  value: number;
  date: string;
  notes: string | null;
}

export interface CSVRowError {
  row: number;
  message: string;
}

export interface CSVImportResult {
  imported: number;
  errors: CSVRowError[];
}

// Dashboard types
export interface ClassSummary {
  id: string;
  name: string;
  grade_level: number;
  student_count: number;
  avg_score: number | null;
  tier_distribution: { tier1: number; tier2: number; tier3: number };
}

export interface AtRiskStudent {
  student_id: string;
  student_name: string;
  class_name: string;
  avg_score: number;
  tier: "tier2" | "tier3";
}

export interface GradeAverage {
  grade_level: number;
  avg_score: number;
  student_count: number;
}

export interface SchoolSummary {
  id: string;
  name: string;
  student_count: number;
  avg_score: number | null;
  tier_distribution: { tier1: number; tier2: number; tier3: number };
  high_risk: boolean;
}

export interface TeacherDashboard {
  classes: ClassSummary[];
  at_risk: AtRiskStudent[];
}

export interface PrincipalDashboard {
  school_name: string;
  total_students: number;
  tier_distribution: { tier1: number; tier2: number; tier3: number };
  classes: ClassSummary[];
  grade_averages: GradeAverage[];
  at_risk: AtRiskStudent[];
}

export interface DistrictDashboard {
  total_students: number;
  tier_distribution: { tier1: number; tier2: number; tier3: number };
  schools: SchoolSummary[];
}
