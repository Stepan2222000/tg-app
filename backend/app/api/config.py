# backend/app/api/config.py
"""
Configuration endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging

from app.utils.config import config
from app.dependencies.auth import get_current_user
from app.db.database import db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """
    Get system configuration (prices, limits, instructions).

    This is a PUBLIC endpoint (no authentication required).
    Returns only client-facing configuration values.

    NEW-CRITICAL-E FIX: Removed internal business logic parameters
    (referral_commission, task_lock_hours) that aren't needed by frontend.

    Returns:
        {
            "simple_task_price": int,
            "phone_task_price": int,
            "min_withdrawal": int,
            "max_active_tasks": int,
            "instructions": str
        }
    """
    return {
        "simple_task_price": config.SIMPLE_TASK_PRICE,
        "phone_task_price": config.PHONE_TASK_PRICE,
        "min_withdrawal": config.MIN_WITHDRAWAL,
        "max_active_tasks": config.MAX_ACTIVE_TASKS,
        "instructions": config.GENERAL_INSTRUCTION
    }


@router.get("/user/me")
async def get_user_me(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get current user data and balances.

    PROTECTED endpoint - requires valid Telegram initData in Authorization header.

    Args:
        user: Current user from get_current_user dependency

    Returns:
        User object with all fields:
        {
            "telegram_id": int,
            "username": str | None,
            "first_name": str,
            "main_balance": int,
            "referral_balance": int,
            "referred_by": int | None,
            "created_at": str (ISO 8601)
        }

    Raises:
        404: If user not found in database
    """
    telegram_id = user["telegram_id"]

    # Query user from database
    user_data = await db.fetch_one(
        "SELECT * FROM users WHERE telegram_id = $1",
        telegram_id
    )

    if not user_data:
        logger.error(f"User {telegram_id} authenticated but not found in database")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please call /auth/init first."
        )

    # Convert created_at to ISO 8601 string
    user_response = dict(user_data)
    if user_response.get("created_at"):
        user_response["created_at"] = user_response["created_at"].isoformat()

    return user_response
