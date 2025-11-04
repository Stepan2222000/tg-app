# backend/app/api/referrals.py
"""
Referral program endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/link")
async def get_referral_link():
    """
    Generate referral link for current user.
    TODO: Implement in Block 17
    """
    return {"message": "Referral link endpoint - to be implemented"}


@router.get("/stats")
async def get_referral_stats():
    """
    Get referral statistics (count and total earnings).
    TODO: Implement in Block 17
    """
    return {"message": "Referral stats endpoint - to be implemented"}


@router.get("/list")
async def get_referral_list():
    """
    Get detailed referral list with earnings breakdown.
    TODO: Implement in Block 17
    """
    return {"message": "Referral list endpoint - to be implemented"}
