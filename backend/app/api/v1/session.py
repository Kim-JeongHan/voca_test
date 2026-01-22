"""
Session API Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.session import (
    SessionStartRequest,
    SessionResponse,
    PromptResponse,
    SubmitRequest,
    SubmitResponse,
    SummaryResponse,
)
from app.services.session_service import SessionService

router = APIRouter()


@router.post("/session/start", response_model=SessionResponse)
async def start_session(
    request: SessionStartRequest,
    db: Session = Depends(get_db)
):
    """
    Start a new quiz session.
    """
    try:
        service = SessionService(db)
        return service.start_session(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.get("/session/{session_id}/prompt", response_model=PromptResponse)
async def get_prompt(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current question for the session.
    """
    try:
        service = SessionService(db)
        return service.get_prompt(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prompt: {str(e)}")


@router.post("/session/{session_id}/submit", response_model=SubmitResponse)
async def submit_answer(
    session_id: int,
    request: SubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Submit answer for current question.
    """
    try:
        service = SessionService(db)
        return service.submit_answer(session_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@router.get("/session/{session_id}/summary", response_model=SummaryResponse)
async def get_summary(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get summary of completed session.
    """
    try:
        service = SessionService(db)
        return service.get_summary(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/session/{session_id}/wrong")
async def get_wrong_words(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get wrong words from a session.
    """
    try:
        from app.models.session import Session as SessionModel

        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        service = SessionService(db)
        wrong_words = service.get_wrong_words(session.deck_id, min_wrong_count=1)

        return {"wrong_words": wrong_words}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get wrong words: {str(e)}")
