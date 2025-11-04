# backend/app/api/withdrawals.py
"""
Withdrawal management endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_withdrawal():
    """
    Create withdrawal request.
    TODO: Implement in Block 16
    """
    return {"message": "Create withdrawal endpoint - to be implemented"}


@router.get("/history")
async def get_withdrawal_history():
    """
    Get withdrawal history for current user.
    TODO: Implement in Block 16
    """
    return {"message": "Withdrawal history endpoint - to be implemented"}
