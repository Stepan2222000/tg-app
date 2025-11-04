# backend/app/api/screenshots.py
"""
Screenshot upload/deletion endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/upload")
async def upload_screenshot():
    """
    Upload screenshot for task assignment.
    TODO: Implement in Block 15
    """
    return {"message": "Screenshot upload endpoint - to be implemented"}


@router.delete("/{screenshot_id}")
async def delete_screenshot():
    """
    Delete screenshot with ownership check.
    TODO: Implement in Block 15
    """
    return {"message": "Screenshot delete endpoint - to be implemented"}
