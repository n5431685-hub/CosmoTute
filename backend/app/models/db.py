"""
Database models and engine setup (SQLModel + SQLite).
"""
from typing import Optional, List
from sqlmodel import Field, SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./cosmotute.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)


# ---------------------------------------------------------------------------
# Table models
# ---------------------------------------------------------------------------

class Skill(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    chapter: str
    class_grade: int = Field(default=8)
    p_l0: float
    p_t: float
    p_s: float
    p_g: float


class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    skill_id: int = Field(foreign_key="skill.id")
    difficulty: int   # 1=easy, 2=medium, 3=hard
    text: str
    options: str      # JSON-encoded list stored as string
    correct_answer: str
    explanation: str
    error_hints: str = Field(default="[]")  # JSON list of hint tags


class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    grade: int
    school: str
    avatar: str = Field(default="🧑‍🎓")


class StudentSkillState(SQLModel, table=True):
    """BKT state: one row per (student, skill) pair."""
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    skill_id: int = Field(foreign_key="skill.id")
    mastery: float = Field(default=0.10)
    opportunities: int = Field(default=0)


class AnswerLog(SQLModel, table=True):
    """Immutable audit log of every submitted answer."""
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    skill_id: int = Field(foreign_key="skill.id")
    question_id: int = Field(foreign_key="question.id")
    student_answer: str
    correct: bool
    mastery_before: float
    mastery_after: float
    error_type: Optional[str] = Field(default=None)  # conceptual/careless/language_confusion
    mode: Optional[str] = Field(default=None)         # learn/solve/test
