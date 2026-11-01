"""FastAPI router: questions."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.models.db import get_session, Question, StudentSkillState, Skill
from app.models.schemas import QuestionOut
from app.core.question_selector import select_next_question

router = APIRouter(prefix="/api", tags=["questions"])


@router.get("/next-question/{student_id}/{skill_id}", response_model=QuestionOut)
def next_question(
    student_id: int,
    skill_id: int,
    mode: Optional[str] = None,
    session: Session = Depends(get_session),
):
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Get current mastery
    state = session.exec(
        select(StudentSkillState).where(
            StudentSkillState.student_id == student_id,
            StudentSkillState.skill_id == skill_id,
        )
    ).first()
    mastery = state.mastery if state else skill.p_l0

    all_questions = [
        {
            "id": q.id,
            "skill_id": q.skill_id,
            "difficulty": q.difficulty,
            "text": q.text,
            "options": json.loads(q.options) if isinstance(q.options, str) else q.options,
            "correct_answer": q.correct_answer,
            "error_hints": json.loads(q.error_hints) if isinstance(q.error_hints, str) else q.error_hints,
        }
        for q in session.exec(select(Question)).all()
    ]

    q = select_next_question(
        questions=all_questions,
        mastery=mastery,
        skill_id=skill_id,
        mode=mode,
    )
    if not q:
        raise HTTPException(status_code=404, detail="No questions available for this skill")

    return QuestionOut(
        id=q["id"],
        skill_id=q["skill_id"],
        difficulty=q["difficulty"],
        text=q["text"],
        options=q["options"],
    )
