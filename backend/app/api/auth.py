# backend/app/api/auth.py
"""
Authentication endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/init")
async def init_user():
    """
    Initialize user (check/create user, handle referral code).
    TODO: Implement in Block 13
    """
    return {"message": "Auth endpoint - to be implemented"}
