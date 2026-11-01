import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000' });

export interface Skill { id: number; name: string; description: string; chapter: string; class_grade: number; }
export interface Student { id: number; name: string; grade: number; school: string; avatar: string; }
export interface Question { id: number; skill_id: number; difficulty: number; text: string; options: string[]; explanation?: string; }
export interface AnswerResponse {
  correct: boolean; mastery_before: number; mastery_after: number;
  mastery_label: string; error_type: string | null;
  explanation: string; next_question: Question | null;
}
export interface StudentMastery { skill_id: number; skill_name: string; mastery: number; mastery_label: string; opportunities: number; }
export interface HeatmapCell { student_id: number; student_name: string; skill_id: number; skill_name: string; mastery: number; mastery_label: string; }
export interface FlaggedStudent { student_id: number; student_name: string; skill_id: number; skill_name: string; mastery: number; opportunities: number; }
export interface ErrorBreakdown { student_id: number; student_name: string; total_errors: number; conceptual: number; careless: number; language_confusion: number; conceptual_pct: number; careless_pct: number; language_confusion_pct: number; }

export const fetchSkills = () => api.get<Skill[]>('/api/skills').then(r => r.data);
export const fetchStudents = () => api.get<Student[]>('/api/students').then(r => r.data);
export const fetchNextQuestion = (studentId: number, skillId: number, mode?: string) =>
  api.get<Question>(`/api/next-question/${studentId}/${skillId}`, { params: mode ? { mode } : {} }).then(r => r.data);
export const submitAnswer = (studentId: number, questionId: number, answer: string, mode?: string) =>
  api.post<AnswerResponse>('/api/answer', { student_id: studentId, question_id: questionId, student_answer: answer, mode }).then(r => r.data);
export const fetchStudentMastery = (studentId: number) =>
  api.get<StudentMastery[]>(`/api/students/${studentId}/mastery`).then(r => r.data);
export const fetchHeatmap = () => api.get<HeatmapCell[]>('/api/dashboard/heatmap').then(r => r.data);
export const fetchFlags = (threshold = 0.4) => api.get<FlaggedStudent[]>('/api/dashboard/flags', { params: { threshold } }).then(r => r.data);
export const fetchErrorBreakdown = (studentId: number) => api.get<ErrorBreakdown>(`/api/dashboard/errors/${studentId}`).then(r => r.data);
