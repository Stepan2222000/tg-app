# backend/app/api/config.py
"""
Configuration endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/config")
async def get_config():
    """
    Get system configuration (prices, limits, instructions).
    TODO: Implement in Block 13
    """
    return {"message": "Config endpoint - to be implemented"}


@router.get("/user/me")
async def get_current_user():
    """
    Get current user data and balances.
    TODO: Implement in Block 13
    """
    return {"message": "User endpoint - to be implemented"}
