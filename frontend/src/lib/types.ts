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

export interface AIAnalysisSnapshot {
  overall_average: number;
  recommended_tier: "tier1" | "tier2" | "tier3";
  student?: { id: string; name: string; grade_level: number };
  class?: { id: string; name: string; grade_level: number };
  subjects: { subject_id: string; average: number; tier: "tier1" | "tier2" | "tier3" }[];
  recent_scores: { date: string; value: number }[];
}

export interface AIRecommendation {
  id: string;
  target_type: "student" | "class";
  student_id: string | null;
  class_id: string | null;
  model_name: string;
  temperature: number;
  response: string;
  snapshot: AIAnalysisSnapshot;
  parse_error: string | null;
  created_at: string;
}

export interface CSVRowError {
  row: number;
  message: string;
}

export interface CSVImportResult {
  imported: number;
  errors: CSVRowError[];
}
