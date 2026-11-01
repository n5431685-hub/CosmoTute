"""FastAPI router: answer submission."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.models.db import get_session
from app.models.schemas import AnswerRequest, AnswerResponse
from app.services.bkt_service import process_answer

router = APIRouter(prefix="/api", tags=["answers"])


@router.post("/answer", response_model=AnswerResponse)
def submit_answer(req: AnswerRequest, session: Session = Depends(get_session)):
    try:
        return process_answer(
            session=session,
            student_id=req.student_id,
            question_id=req.question_id,
            student_answer=req.student_answer,
            mode=req.mode,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
