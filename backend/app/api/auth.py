# backend/app/api/auth.py
"""
Authentication endpoints.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.dependencies.auth import get_current_user, hash_user_id
from app.db.database import db
from app.utils.datetime import to_iso8601
from app.utils.rate_limit import limiter

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/init")
@limiter.limit("10/minute")  # Max 10 requests per minute per IP
async def init_user(
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Initialize user (check/create user, update username/first_name if changed).

    PROTECTED endpoint - requires valid Telegram initData in Authorization header.

    RATE LIMITED: 10 requests per minute per IP to prevent abuse.

    This endpoint handles:
    1. First-time user registration
    2. Returning user login (with smart update of username/first_name if changed)

    NOTE: Referral logic is handled by Telegram bot (/start command).
          The bot sets referred_by BEFORE Mini App opens.

    Args:
        user: Current user from get_current_user dependency (telegram_id, username, first_name)

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
      - INSERT new user (referred_by will be NULL unless set by bot)
    - If user EXISTS in DB:
      - UPDATE username/first_name if changed
      - referred_by is NOT updated (immutable, set only by bot)
    """
    telegram_id = user["telegram_id"]
    username = user.get("username")
    first_name = user.get("first_name", "")

    logger.info(f"[DIAG] ======================================")
    logger.info(f"[DIAG] /api/auth/init endpoint called")
    logger.info(f"[DIAG] telegram_id (hashed): {hash_user_id(telegram_id)}")
    logger.info(f"[DIAG] username: {username if username else 'none'}")
    logger.info(f"[DIAG] first_name length: {len(first_name) if first_name else 0}")

    # Log with hashed ID (GDPR compliant)
    logger.info(f"init_user called for telegram_id={hash_user_id(telegram_id)}")

    # Use UPSERT to handle both new user registration and existing user update atomically
    # This prevents race condition when multiple requests arrive simultaneously
    # NOTE: referred_by is NOT touched here (set only by Telegram bot)
    logger.info(f"[DIAG] Executing UPSERT query...")

    import time
    upsert_start = time.time()

    try:
        user_data = await db.fetch_one(
            """
            INSERT INTO users (telegram_id, username, first_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (telegram_id) DO UPDATE
            SET username = EXCLUDED.username,
                first_name = EXCLUDED.first_name
            RETURNING *
            """,
            telegram_id,
            username,
            first_name
        )

        upsert_time = (time.time() - upsert_start) * 1000  # Convert to ms
        logger.info(f"[DIAG] UPSERT completed in {upsert_time:.2f}ms")

        # Log whether this was insert or update
        if user_data:
            logger.info(f"[DIAG] UPSERT returned user data successfully")

            # Check if this was a new user or existing user
            existing_check = await db.fetch_val(
                "SELECT COUNT(*) FROM users WHERE telegram_id = $1 AND created_at < NOW() - INTERVAL '1 second'",
                telegram_id
            )
            if existing_check > 0:
                logger.info(f"[DIAG] Path: EXISTING USER (UPDATE)")
                logger.info(f"Existing user login: telegram_id={hash_user_id(telegram_id)}")
            else:
                logger.info(f"[DIAG] Path: NEW USER (INSERT)")
                logger.info(f"New user registered: telegram_id={hash_user_id(telegram_id)}")

        logger.info(f"[DIAG] Returning user data to client...")
        logger.info(f"[DIAG] ======================================")
    except Exception as e:
        logger.error(f"[DIAG] ======================================")
        logger.error(f"[DIAG] EXCEPTION OCCURRED in UPSERT")
        logger.error(f"[DIAG] Exception type: {type(e).__name__}")
        logger.error(f"[DIAG] Exception message: {str(e)}")
        logger.error(f"[DIAG] ======================================")
        logger.error(f"Failed to upsert user {hash_user_id(telegram_id)}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize user"
        )

    # Convert created_at to ISO 8601 string
    user_response = dict(user_data)
    if user_response.get("created_at"):
        user_response["created_at"] = to_iso8601(user_response["created_at"])

    return user_response
