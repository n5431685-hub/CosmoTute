"""FastAPI router: teacher dashboard."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.models.db import get_session
from app.models.schemas import HeatmapCell, FlaggedStudent, ErrorBreakdown
from app.services.dashboard_service import (
    get_heatmap, get_flagged_students, get_error_breakdown
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/heatmap", response_model=List[HeatmapCell])
def heatmap(session: Session = Depends(get_session)):
    return get_heatmap(session)


@router.get("/flags", response_model=List[FlaggedStudent])
def flags(threshold: float = 0.40, session: Session = Depends(get_session)):
    return get_flagged_students(session, threshold=threshold)


@router.get("/errors/{student_id}", response_model=ErrorBreakdown)
def errors(student_id: int, session: Session = Depends(get_session)):
    try:
        return get_error_breakdown(session, student_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
