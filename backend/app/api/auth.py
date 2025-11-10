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

    NOTE: Referral logic is handled in TWO ways:
          1. Telegram Bot /start command (traditional bot flow)
          2. Direct Link Mini App start_param (direct WebApp launch via LAUNCH APP button)
          This endpoint processes start_param for Direct Link scenario.

    Args:
        user: Current user from get_current_user dependency
              (telegram_id, username, first_name, start_param)

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
    - Parse start_param (format: ref_TELEGRAM_ID) to extract referrer
    - Validate referrer (not self-referral, exists in DB)
    - If user does NOT exist in DB:
      - INSERT new user with referred_by from start_param
    - If user EXISTS in DB:
      - UPDATE username/first_name if changed
      - referred_by is NOT updated (immutable, set only once on first registration)
    """
    telegram_id = user["telegram_id"]
    username = user.get("username")
    first_name = user.get("first_name", "")
    start_param = user.get("start_param")

    # Parse referral code from start_param (format: ref_TELEGRAM_ID)
    referred_by = None
    if start_param and start_param.startswith('ref_'):
        try:
            referred_by = int(start_param.replace('ref_', ''))

            # Validate: not self-referral (database has CHECK constraint, but validate early)
            if referred_by == telegram_id:
                logger.warning(f"Self-referral blocked: user={hash_user_id(telegram_id)}")
                referred_by = None
            else:
                # Validate: referrer exists in database
                referrer = await db.fetch_one(
                    "SELECT telegram_id FROM users WHERE telegram_id = $1",
                    referred_by
                )
                if not referrer:
                    logger.warning(
                        f"Referrer not found: user={hash_user_id(telegram_id)}, "
                        f"referrer={hash_user_id(referred_by)}"
                    )
                    referred_by = None
                else:
                    logger.info(
                        f"Valid referral detected: user={hash_user_id(telegram_id)} "
                        f"→ referrer={hash_user_id(referred_by)}"
                    )
        except ValueError:
            logger.warning(f"Invalid start_param format: {start_param}")
            referred_by = None

    logger.info(f"[DIAG] ======================================")
    logger.info(f"[DIAG] /api/auth/init endpoint called")
    logger.info(f"[DIAG] telegram_id (hashed): {hash_user_id(telegram_id)}")
    logger.info(f"[DIAG] username: {username if username else 'none'}")
    logger.info(f"[DIAG] first_name length: {len(first_name) if first_name else 0}")
    logger.info(f"[DIAG] start_param: {start_param if start_param else 'none'}")
    logger.info(f"[DIAG] referred_by (hashed): {hash_user_id(referred_by) if referred_by else 'none'}")

    # Log with hashed ID (GDPR compliant)
    logger.info(f"init_user called for telegram_id={hash_user_id(telegram_id)}")

    # Use UPSERT to handle both new user registration and existing user update atomically
    # This prevents race condition when multiple requests arrive simultaneously
    # NOTE: referred_by is set on first registration (immutable after that)
    logger.info(f"[DIAG] Executing UPSERT query...")

    import time
    upsert_start = time.time()

    try:
        user_data = await db.fetch_one(
            """
            INSERT INTO users (telegram_id, username, first_name, referred_by)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (telegram_id) DO UPDATE
            SET username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                referred_by = CASE
                    WHEN users.referred_by IS NULL THEN EXCLUDED.referred_by
                    ELSE users.referred_by
                END
            RETURNING *
            """,
            telegram_id,
            username,
            first_name,
            referred_by
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
