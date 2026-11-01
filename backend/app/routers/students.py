"""FastAPI router: students."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.models.db import get_session, Student, StudentSkillState, Skill
from app.models.schemas import StudentMastery
from app.core.bkt import mastery_level_label

router = APIRouter(prefix="/api", tags=["students"])


@router.get("/students")
def list_students(session: Session = Depends(get_session)):
    students = session.exec(select(Student)).all()
    return [{"id": s.id, "name": s.name, "grade": s.grade, "school": s.school, "avatar": s.avatar}
            for s in students]


@router.get("/students/{student_id}/mastery", response_model=List[StudentMastery])
def student_mastery(student_id: int, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    skills = session.exec(select(Skill)).all()
    result = []
    for skill in skills:
        state = session.exec(
            select(StudentSkillState).where(
                StudentSkillState.student_id == student_id,
                StudentSkillState.skill_id == skill.id,
            )
        ).first()
        mastery = state.mastery if state else skill.p_l0
        opps    = state.opportunities if state else 0
        result.append(StudentMastery(
            skill_id=skill.id,
            skill_name=skill.name,
            mastery=round(mastery, 4),
            mastery_label=mastery_level_label(mastery),
            opportunities=opps,
        ))
    return result
