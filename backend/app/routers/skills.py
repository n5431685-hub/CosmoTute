"""FastAPI router: skills."""
from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.models.db import get_session, Skill
from app.models.schemas import SkillOut

router = APIRouter(prefix="/api", tags=["skills"])


@router.get("/skills", response_model=List[SkillOut])
def list_skills(session: Session = Depends(get_session)):
    skills = session.exec(select(Skill)).all()
    return [SkillOut(
        id=s.id,
        name=s.name,
        description=s.description,
        chapter=s.chapter,
        class_grade=s.class_grade,
    ) for s in skills]
