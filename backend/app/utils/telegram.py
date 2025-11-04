# backend/app/utils/telegram.py
"""
Telegram Web App initData validation.
Implements HMAC-SHA256 signature verification according to Telegram documentation.
"""

import hmac
import hashlib
import json
import time
from typing import Dict, Any, Optional
from urllib.parse import unquote, parse_qs
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

# Maximum age of initData in seconds (1 hour)
# Balances security (short window) with UX (app can stay open)
MAX_AUTH_AGE = 3600

# Clock skew tolerance in seconds (to handle minor time differences)
CLOCK_SKEW_TOLERANCE = 60


def parse_init_data(init_data: str) -> Dict[str, str]:
    """
    Parse Telegram initData query string.

    Args:
        init_data: Query string from Telegram.WebApp.initData

    Returns:
        Dictionary of parsed and URL-decoded parameters

    Example:
        "query_id=xxx&user=%7B%22id%22%3A12345%7D&hash=abc"
        -> {"query_id": "xxx", "user": '{"id":12345}', "hash": "abc"}
    """
    parsed = {}
    for item in init_data.split('&'):
        if '=' in item:
            key, value = item.split('=', 1)
            parsed[key] = unquote(value)
    return parsed


def validate_init_data(
    init_data: str,
    bot_token: str,
    max_age: int = MAX_AUTH_AGE
) -> Dict[str, Any]:
    """
    Validate Telegram Web App initData using HMAC-SHA256.

    Algorithm (from Telegram docs):
    1. Parse initData as query string
    2. Extract hash parameter
    3. Create data_check_string (all params except hash, sorted, joined with \\n)
    4. secret_key = HMAC-SHA256(bot_token, key="WebAppData")
    5. calculated_hash = HMAC-SHA256(data_check_string, key=secret_key)
    6. Verify: calculated_hash == received_hash
    7. Check auth_date is not expired

    Args:
        init_data: Raw initData string from Telegram.WebApp.initData
        bot_token: Telegram bot token (from config)
        max_age: Maximum age of initData in seconds (default: 3600)

    Returns:
        Parsed user data dictionary:
        {
            "telegram_id": int,
            "username": str | None,
            "first_name": str,
            "last_name": str | None,
            "start_param": str | None  # For referral codes
        }

    Raises:
        HTTPException(401): If validation fails or data is expired

    Example:
        user = validate_init_data(request.headers["Authorization"].split(" ")[1], bot_token)
        telegram_id = user["telegram_id"]
    """
    # Parse initData
    try:
        parsed = parse_init_data(init_data)
    except Exception as e:
        logger.error(f"Failed to parse initData: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid initData format"
        )

    # Extract hash
    received_hash = parsed.get('hash')
    if not received_hash:
        logger.error("Missing hash in initData")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing hash parameter"
        )

    # Check auth_date
    auth_date_str = parsed.get('auth_date')
    if not auth_date_str:
        logger.error("Missing auth_date in initData")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing auth_date parameter"
        )

    try:
        auth_date = int(auth_date_str)
    except ValueError:
        logger.error(f"Invalid auth_date format: {auth_date_str}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid auth_date format"
        )

    # Verify auth_date is valid (not in the future, not expired)
    current_time = int(time.time())
    age = current_time - auth_date

    # Check for future timestamps (clock skew attack protection)
    if age < -CLOCK_SKEW_TOLERANCE:
        logger.warning(f"Future timestamp detected: {-age}s ahead (user: {parsed.get('user', 'unknown')[:20]})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication expired. Please reload the application."
        )

    # Check for expired timestamps
    if age > max_age:
        logger.warning(f"Expired initData detected (user: {parsed.get('user', 'unknown')[:20]})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication expired. Please reload the application."
        )

    # Create data_check_string
    # All parameters except 'hash', sorted alphabetically, joined with \n
    data_check_items = []
    for key in sorted(parsed.keys()):
        if key != 'hash':
            data_check_items.append(f"{key}={parsed[key]}")
    data_check_string = '\n'.join(data_check_items)

    # Step 1: Create secret_key = HMAC-SHA256 with key="WebAppData", message=bot_token
    # As per Telegram spec: the bot token is the message, "WebAppData" is the key
    secret_key = hmac.new(
        key="WebAppData".encode('utf-8'),
        msg=bot_token.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()

    # Step 2: Calculate hash = HMAC-SHA256(data_check_string, key=secret_key)
    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

    # Verify hash using constant-time comparison (timing attack protection)
    if not hmac.compare_digest(calculated_hash, received_hash):
        logger.warning("Hash verification failed (invalid signature)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    # Parse user data
    user_json = parsed.get('user')
    if not user_json:
        logger.error("Missing user data in initData")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user data"
        )

    try:
        user_data = json.loads(user_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse user JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data format"
        )

    # Extract user fields
    telegram_id = user_data.get('id')
    if not telegram_id:
        logger.error("Missing user id in initData")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user id"
        )

    # Extract start_param (for referral codes like "ref_12345678")
    start_param = parsed.get('start_param')

    result = {
        "telegram_id": telegram_id,
        "username": user_data.get('username'),
        "first_name": user_data.get('first_name', ''),
        "last_name": user_data.get('last_name'),
        "start_param": start_param
    }

    logger.info(f"Successfully validated initData for user {telegram_id}")
    return result
