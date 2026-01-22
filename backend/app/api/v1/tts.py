"""
TTS API Router
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.tts import TTSRequest, TTSResponse
from app.services.tts_service import TTSService

router = APIRouter()


@router.post("/tts", response_model=TTSResponse)
async def generate_tts(
    request: TTSRequest,
    db: Session = Depends(get_db)
):
    """
    Generate TTS audio for given text.
    Returns audio/mpeg binary data or error.
    """
    try:
        service = TTSService(db)
        audio_data, content_type = await service.get_tts_audio(request.text)

        # Return audio binary
        return Response(
            content=audio_data,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=31536000, immutable"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
