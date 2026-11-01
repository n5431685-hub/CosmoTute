"""
BKT Service
============
Orchestrates BKT updates against the database.
"""
import json
from typing import List, Optional

from sqlmodel import Session, select

from app.models.db import (
    Skill, Question, Student, StudentSkillState, AnswerLog
)
from app.models.schemas import AnswerResponse, QuestionOut
from app.core.bkt import BKTParams, BKTState, bkt_update, mastery_level_label
from app.core.question_selector import select_next_question
from app.core.error_tagger import tag_error


def _get_or_create_state(
    session: Session, student_id: int, skill_id: int, p_l0: float
) -> StudentSkillState:
    stmt = select(StudentSkillState).where(
        StudentSkillState.student_id == student_id,
        StudentSkillState.skill_id == skill_id,
    )
    state = session.exec(stmt).first()
    if not state:
        state = StudentSkillState(
            student_id=student_id,
            skill_id=skill_id,
            mastery=p_l0,
            opportunities=0,
        )
        session.add(state)
        session.commit()
        session.refresh(state)
    return state


def process_answer(
    session: Session,
    student_id: int,
    question_id: int,
    student_answer: str,
    mode: Optional[str],
) -> AnswerResponse:
    # Load question
    question = session.get(Question, question_id)
    if not question:
        raise ValueError(f"Question {question_id} not found")

    # Load skill and its BKT params
    skill = session.get(Skill, question.skill_id)
    if not skill:
        raise ValueError(f"Skill {question.skill_id} not found")

    params = BKTParams(p_l0=skill.p_l0, p_t=skill.p_t, p_s=skill.p_s, p_g=skill.p_g)

    # Load current BKT state
    db_state = _get_or_create_state(session, student_id, skill.id, skill.p_l0)
    mastery_before = db_state.mastery

    # Evaluate correctness
    correct = student_answer.strip().lower() == question.correct_answer.strip().lower()

    # BKT update
    bkt_state = BKTState(mastery=mastery_before, opportunities=db_state.opportunities)
    bkt_state = bkt_update(bkt_state, params, correct)
    mastery_after = bkt_state.mastery

    # Tag error (only on wrong answers)
    error_type = tag_error(
        correct=correct,
        mastery=mastery_before,
        difficulty=question.difficulty,
        question_text=question.text,
        student_answer=student_answer,
        error_hints=json.loads(question.error_hints),
    )

    # Persist updated state
    db_state.mastery = mastery_after
    db_state.opportunities = bkt_state.opportunities
    session.add(db_state)

    # Log answer
    log = AnswerLog(
        student_id=student_id,
        skill_id=skill.id,
        question_id=question_id,
        student_answer=student_answer,
        correct=correct,
        mastery_before=mastery_before,
        mastery_after=mastery_after,
        error_type=error_type,
        mode=mode,
    )
    session.add(log)
    session.commit()

    # Select next question (exclude current)
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

    # Get recently seen question ids for this student/skill (last 5)
    recent_logs = session.exec(
        select(AnswerLog).where(
            AnswerLog.student_id == student_id,
            AnswerLog.skill_id == skill.id,
        ).order_by(AnswerLog.id.desc()).limit(5)
    ).all()
    recently_seen = [l.question_id for l in recent_logs]

    next_q_dict = select_next_question(
        questions=all_questions,
        mastery=mastery_after,
        skill_id=skill.id,
        mode=mode,
        recently_seen_ids=recently_seen,
    )

    next_question = None
    if next_q_dict:
        next_question = QuestionOut(
            id=next_q_dict["id"],
            skill_id=next_q_dict["skill_id"],
            difficulty=next_q_dict["difficulty"],
            text=next_q_dict["text"],
            options=next_q_dict["options"],
        )

    return AnswerResponse(
        correct=correct,
        mastery_before=round(mastery_before, 4),
        mastery_after=round(mastery_after, 4),
        mastery_label=mastery_level_label(mastery_after),
        error_type=error_type,
        explanation=question.explanation,
        next_question=next_question,
    )
