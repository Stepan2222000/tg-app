# backend/app/dependencies/auth.py
"""
Authentication dependency for FastAPI endpoints.
Validates Telegram Web App initData from Authorization header.
"""

from typing import Dict, Any
from fastapi import Request, HTTPException, status
import logging
import hashlib

from app.utils.telegram import validate_init_data
from app.utils.config import config

logger = logging.getLogger(__name__)


# CRITICAL-6 FIX: Hash user ID for GDPR-compliant logging
def hash_user_id(telegram_id: int) -> str:
    """Create privacy-safe user identifier for logs (GDPR compliant)."""
    return hashlib.sha256(str(telegram_id).encode()).hexdigest()[:12]


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and validate current user from Telegram initData.

    Expected Authorization header format: "tma {initData}"
    where {initData} is the string from Telegram.WebApp.initData

    Args:
        request: FastAPI Request object

    Returns:
        User data dictionary:
        {
            "telegram_id": int,
            "username": str | None,
            "first_name": str,
            "last_name": str | None,
            "start_param": str | None
        }

    Raises:
        HTTPException(401): If Authorization header is missing or invalid

    Usage:
        @router.get("/protected")
        async def protected_endpoint(user: dict = Depends(get_current_user)):
            telegram_id = user["telegram_id"]
            return {"message": f"Hello, {user['first_name']}!"}
    """
    logger.info(f"[DIAG] --- get_current_user() called ---")
    logger.info(f"[DIAG] Request path: {request.url.path}")

    # Extract Authorization header
    authorization = request.headers.get("Authorization")
    logger.info(f"[DIAG] Authorization header present: {authorization is not None}")

    if not authorization:
        logger.error("[DIAG] ERROR: No Authorization header!")
        logger.warning("Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )

    logger.info(f"[DIAG] Authorization header length: {len(authorization)}")

    # Check format: "tma {initData}"
    parts = authorization.split(" ", 1)
    logger.info(f"[DIAG] Authorization split into {len(parts)} parts")

    if len(parts) != 2 or parts[0].lower() != "tma":
        logger.error(f"[DIAG] ERROR: Invalid format. Parts: {len(parts)}, First part: {parts[0] if parts else 'none'}")
        logger.warning("Invalid Authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Authorization header format. Expected: "tma {initData}"'
        )

    init_data = parts[1]
    logger.info(f"[DIAG] initData extracted, length: {len(init_data)}")

    if len(init_data) == 0:
        logger.error(f"[DIAG] ERROR: initData is EMPTY STRING!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData is empty"
        )

    # Validate initData using HMAC-SHA256
    logger.info(f"[DIAG] Calling validate_init_data()...")

    try:
        import time
        validate_start = time.time()

        user_data = validate_init_data(
            init_data=init_data,
            bot_token=config.TELEGRAM_BOT_TOKEN
        )

        validate_time = (time.time() - validate_start) * 1000  # Convert to ms
        logger.info(f"[DIAG] validate_init_data() completed in {validate_time:.2f}ms")

        # CRITICAL-6 FIX: Hash telegram_id for GDPR-compliant logging
        logger.info(f"[DIAG] User authenticated successfully: {hash_user_id(user_data['telegram_id'])}")
        logger.info(f"[DIAG] User data keys: {list(user_data.keys())}")
        logger.info(f"[DIAG] --- get_current_user() SUCCESS ---")
        logger.debug(f"User authenticated: {hash_user_id(user_data['telegram_id'])}")
        return user_data
    except HTTPException as e:
        logger.error(f"[DIAG] --- get_current_user() FAILED (HTTPException) ---")
        logger.error(f"[DIAG] Status code: {e.status_code}")
        logger.error(f"[DIAG] Detail: {e.detail}")
        # Re-raise HTTPException from validate_init_data
        raise
    except Exception as e:
        logger.error(f"[DIAG] --- get_current_user() FAILED (Exception) ---")
        logger.error(f"[DIAG] Exception type: {type(e).__name__}")
        logger.error(f"[DIAG] Exception message: {str(e)}")
        logger.error(f"Unexpected error during initData validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to validate initData"
        )
