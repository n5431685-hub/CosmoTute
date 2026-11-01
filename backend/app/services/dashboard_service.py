"""
Dashboard Service
==================
Aggregates data for the teacher dashboard.
"""
from typing import List
from sqlmodel import Session, select

from app.models.db import (
    Skill, Student, StudentSkillState, AnswerLog
)
from app.models.schemas import HeatmapCell, FlaggedStudent, ErrorBreakdown
from app.core.bkt import mastery_level_label
from app.core.error_tagger import error_summary


def get_heatmap(session: Session) -> List[HeatmapCell]:
    """Return skill × student mastery matrix."""
    students = session.exec(select(Student)).all()
    skills   = session.exec(select(Skill)).all()

    cells = []
    for student in students:
        for skill in skills:
            stmt = select(StudentSkillState).where(
                StudentSkillState.student_id == student.id,
                StudentSkillState.skill_id == skill.id,
            )
            state = session.exec(stmt).first()
            mastery = state.mastery if state else skill.p_l0

            cells.append(HeatmapCell(
                student_id=student.id,
                student_name=student.name,
                skill_id=skill.id,
                skill_name=skill.name,
                mastery=round(mastery, 4),
                mastery_label=mastery_level_label(mastery),
            ))
    return cells


def get_flagged_students(session: Session, threshold: float = 0.40) -> List[FlaggedStudent]:
    """Return students below mastery threshold for any skill (min 5 attempts)."""
    flagged = []
    students = session.exec(select(Student)).all()
    skills   = session.exec(select(Skill)).all()

    for student in students:
        for skill in skills:
            stmt = select(StudentSkillState).where(
                StudentSkillState.student_id == student.id,
                StudentSkillState.skill_id == skill.id,
            )
            state = session.exec(stmt).first()
            if state and state.opportunities >= 3 and state.mastery < threshold:
                flagged.append(FlaggedStudent(
                    student_id=student.id,
                    student_name=student.name,
                    skill_id=skill.id,
                    skill_name=skill.name,
                    mastery=round(state.mastery, 4),
                    opportunities=state.opportunities,
                ))
    return flagged


def get_error_breakdown(session: Session, student_id: int) -> ErrorBreakdown:
    """Return error-type breakdown for a student."""
    student = session.get(Student, student_id)
    if not student:
        raise ValueError(f"Student {student_id} not found")

    logs = session.exec(
        select(AnswerLog).where(
            AnswerLog.student_id == student_id,
            AnswerLog.correct == False,
            AnswerLog.error_type != None,
        )
    ).all()

    error_types = [l.error_type for l in logs if l.error_type]
    summary = error_summary(error_types)

    return ErrorBreakdown(
        student_id=student_id,
        student_name=student.name,
        **summary,
    )
