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
