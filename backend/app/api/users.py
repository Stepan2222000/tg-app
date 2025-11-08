# backend/app/api/users.py
"""
User endpoints.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user, hash_user_id
from app.db.database import db
from app.utils.datetime import to_iso8601

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me")
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
        logger.error(f"User {hash_user_id(telegram_id)} authenticated but not found in database")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please call /auth/init first."
        )

    # Convert created_at to ISO 8601 string
    user_response = dict(user_data)
    if user_response.get("created_at"):
        user_response["created_at"] = to_iso8601(user_response["created_at"])

    return user_response
