# -*- coding: utf-8 -*-
"""
Image API Router

NOTE: Image generation is currently disabled.
Will be re-implemented with local Stable Diffusion support.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/image")
async def generate_image():
    """
    Generate association image for given word.
    Currently disabled - returns 501 Not Implemented.
    """
    raise HTTPException(
        status_code=501,
        detail="Image generation is currently disabled. Will be available in future release.",
    )


@router.post("/image/github")
async def commit_image_to_github():
    """
    Commit generated image to GitHub repository.
    Currently disabled - returns 501 Not Implemented.
    """
    raise HTTPException(
        status_code=501, detail="GitHub image commit is currently disabled."
    )
