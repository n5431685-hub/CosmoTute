"""Pydantic request/response schemas (separate from DB models)."""
from typing import List, Optional
from pydantic import BaseModel


class AnswerRequest(BaseModel):
    student_id: int
    question_id: int
    student_answer: str
    mode: Optional[str] = None   # 'learn' | 'solve' | 'test'


class QuestionOut(BaseModel):
    id: int
    skill_id: int
    difficulty: int
    text: str
    options: List[str]
    explanation: Optional[str] = None   # only returned after answering


class AnswerResponse(BaseModel):
    correct: bool
    mastery_before: float
    mastery_after: float
    mastery_label: str          # at_risk / struggling / proficient / mastered
    error_type: Optional[str]   # conceptual / careless / language_confusion
    explanation: str
    next_question: Optional[QuestionOut]


class StudentMastery(BaseModel):
    skill_id: int
    skill_name: str
    mastery: float
    mastery_label: str
    opportunities: int


class HeatmapCell(BaseModel):
    student_id: int
    student_name: str
    skill_id: int
    skill_name: str
    mastery: float
    mastery_label: str


class FlaggedStudent(BaseModel):
    student_id: int
    student_name: str
    skill_id: int
    skill_name: str
    mastery: float
    opportunities: int


class ErrorBreakdown(BaseModel):
    student_id: int
    student_name: str
    total_errors: int
    conceptual: int
    careless: int
    language_confusion: int
    conceptual_pct: float
    careless_pct: float
    language_confusion_pct: float


class SkillOut(BaseModel):
    id: int
    name: str
    description: str
    chapter: str
    class_grade: int
