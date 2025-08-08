"""
Additional models for the FastAPI backend
"""
from pydantic import BaseModel, Field
from typing import Optional

class DeleteFileRequest(BaseModel):
    """Request model for deleting a file"""
    file_path: str = Field(..., description="Path to the file to delete")

class DeleteFileResponse(BaseModel):
    """Response model for delete operations"""
    success: bool = Field(..., description="Whether the deletion was successful")
    message: Optional[str] = Field(None, description="Optional status message")
    file_path: str = Field(..., description="Path of the deleted file")