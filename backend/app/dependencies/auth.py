# backend/app/dependencies/auth.py
"""
Authentication dependency for FastAPI endpoints.
Validates Telegram Web App initData from Authorization header.
"""

from typing import Dict, Any
from fastapi import Request, HTTPException, status
import logging

from app.utils.telegram import validate_init_data
from app.utils.config import config

logger = logging.getLogger(__name__)


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
    # Extract Authorization header
    authorization = request.headers.get("Authorization")

    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )

    # Check format: "tma {initData}"
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "tma":
        logger.warning("Invalid Authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Authorization header format. Expected: "tma {initData}"'
        )

    init_data = parts[1]

    # Validate initData using HMAC-SHA256
    try:
        user_data = validate_init_data(
            init_data=init_data,
            bot_token=config.TELEGRAM_BOT_TOKEN
        )
        logger.debug(f"User authenticated: {user_data['telegram_id']}")
        return user_data
    except HTTPException:
        # Re-raise HTTPException from validate_init_data
        raise
    except Exception as e:
        logger.error(f"Unexpected error during initData validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to validate initData"
        )
