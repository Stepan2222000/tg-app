# backend/app/api/auth.py
"""
Authentication endpoints.
"""

import logging
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.db.database import db
from app.utils.datetime import to_iso8601

router = APIRouter()
logger = logging.getLogger(__name__)


def parse_referral_code(start_param: Optional[str]) -> Optional[int]:
    """
    Parse referral code from start_param.

    Expected format: "ref_TELEGRAM_ID" (e.g., "ref_12345678")

    Args:
        start_param: Start parameter from Telegram initData

    Returns:
        Referrer telegram_id as integer, or None if invalid/missing

    Example:
        parse_referral_code("ref_12345678") -> 12345678
        parse_referral_code("invalid") -> None
        parse_referral_code(None) -> None
    """
    if not start_param:
        return None

    # Match pattern: ref_DIGITS
    match = re.match(r'^ref_(\d+)$', start_param)
    if not match:
        logger.warning(f"Invalid referral code format: {start_param}")
        return None

    try:
        referrer_id = int(match.group(1))
        return referrer_id
    except ValueError:
        logger.warning(f"Failed to parse referrer_id from: {start_param}")
        return None


@router.post("/init")
async def init_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Initialize user (check/create user, handle referral code).

    PROTECTED endpoint - requires valid Telegram initData in Authorization header.

    This endpoint handles:
    1. First-time user registration (with optional referral code)
    2. Returning user login (with smart update of username/first_name if changed)

    Args:
        user: Current user from get_current_user dependency (telegram_id, username, first_name, start_param)

    Returns:
        User object:
        {
            "telegram_id": int,
            "username": str | None,
            "first_name": str,
            "main_balance": int,
            "referral_balance": int,
            "referred_by": int | None,
            "created_at": str (ISO 8601)
        }

    Logic:
    - If user does NOT exist in DB:
      - Parse referral code from start_param (format: ref_TELEGRAM_ID)
      - INSERT new user with referred_by
    - If user EXISTS in DB:
      - Compare username/first_name with DB values
      - UPDATE only if changed (smart update)
      - Note: referred_by is IMMUTABLE (only set on first registration)
    """
    telegram_id = user["telegram_id"]
    username = user.get("username")
    first_name = user.get("first_name", "")
    start_param = user.get("start_param")

    logger.info(f"init_user called for telegram_id={telegram_id}, start_param={start_param}")

    # Parse referral code (format: ref_TELEGRAM_ID)
    referred_by = parse_referral_code(start_param)

    # Validate referral code
    if referred_by:
        # Check for self-referral
        if referred_by == telegram_id:
            logger.warning(f"User {telegram_id} attempted self-referral, ignoring")
            referred_by = None
        else:
            # Verify referrer exists
            referrer = await db.fetch_one(
                "SELECT telegram_id FROM users WHERE telegram_id = $1",
                referred_by
            )
            if not referrer:
                logger.warning(f"Referrer {referred_by} not found, ignoring referral")
                referred_by = None
            else:
                logger.info(f"User {telegram_id} referred by {referred_by}")

    # Use UPSERT to handle both new user registration and existing user update atomically
    # This prevents race condition when multiple requests arrive simultaneously
    try:
        user_data = await db.fetch_one(
            """
            INSERT INTO users (telegram_id, username, first_name, referred_by)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (telegram_id) DO UPDATE
            SET username = EXCLUDED.username,
                first_name = EXCLUDED.first_name
            RETURNING *
            """,
            telegram_id,
            username,
            first_name,
            referred_by
        )

        # Log whether this was insert or update
        if user_data:
            # Check if this was a new user (referred_by was just set) or existing user
            existing_check = await db.fetch_val(
                "SELECT COUNT(*) FROM users WHERE telegram_id = $1 AND created_at < NOW() - INTERVAL '1 second'",
                telegram_id
            )
            if existing_check > 0:
                logger.info(f"Existing user login: telegram_id={telegram_id}")
            else:
                logger.info(f"New user registered: telegram_id={telegram_id}, referred_by={referred_by}")
    except Exception as e:
        logger.error(f"Failed to upsert user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize user"
        )

    # Convert created_at to ISO 8601 string
    user_response = dict(user_data)
    if user_response.get("created_at"):
        user_response["created_at"] = to_iso8601(user_response["created_at"])

    return user_response
