from pydantic import BaseModel, Field
from typing import Optional


class ImageRequest(BaseModel):
    word: str = Field(..., max_length=50, description="Word to generate image for")


class ImageResponse(BaseModel):
    image_url: Optional[str] = Field(None, description="URL to image if available")
    github_url: Optional[str] = Field(None, description="GitHub URL if committed")
    error: Optional[str] = Field(None, description="Error message if any")


class GitHubCommitRequest(BaseModel):
    word: str = Field(..., max_length=50, description="Word identifier")
    image_base64: str = Field(..., description="Base64 encoded image data")


class GitHubCommitResponse(BaseModel):
    success: bool
    url: Optional[str] = Field(None, description="URL to committed file")
    path: Optional[str] = Field(None, description="Path in repository")
    error: Optional[str] = Field(None, description="Error message if any")
