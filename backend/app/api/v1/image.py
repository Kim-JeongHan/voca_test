"""
Image API Router
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.image import ImageRequest, ImageResponse, GitHubCommitRequest, GitHubCommitResponse
from app.services.image_service import ImageService

router = APIRouter()


@router.post("/image")
async def generate_image(
    request: ImageRequest,
    db: Session = Depends(get_db)
):
    """
    Generate association image for given word.
    Returns image/png binary data.
    """
    try:
        service = ImageService(db)
        image_data, content_type, github_url = await service.get_image(request.word)

        # Return image binary
        return Response(
            content=image_data,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
                "X-GitHub-URL": github_url or ""
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/image/github", response_model=GitHubCommitResponse)
async def commit_image_to_github(
    request: GitHubCommitRequest,
    db: Session = Depends(get_db)
):
    """
    Commit generated image to GitHub repository.
    """
    try:
        import base64

        service = ImageService(db)

        # Decode base64 image
        image_data = base64.b64decode(request.image_base64)

        # Commit to GitHub
        github_url = await service.commit_to_github(request.word, image_data)

        return GitHubCommitResponse(
            success=True,
            url=github_url,
            path=f"docs/images/{request.word}.png"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return GitHubCommitResponse(
            success=False,
            error=f"GitHub commit failed: {str(e)}"
        )
