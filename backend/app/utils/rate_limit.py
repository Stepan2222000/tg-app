# backend/app/utils/rate_limit.py
"""
Rate limiting configuration using slowapi.
Implements combined rate limiting by IP + telegram_id to prevent abuse.
"""

import json
from urllib.parse import unquote
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_user_identifier(request: Request) -> str:
    """
    Rate limit key: IP + telegram_id (if available).

    This provides better rate limiting by combining IP address with user identity,
    preventing both IP-based and user-based abuse while avoiding blocking
    legitimate users behind shared NAT.

    Args:
        request: FastAPI Request object

    Returns:
        Rate limit key in format:
        - "{ip}:{telegram_id}" if telegram_id can be extracted
        - "{ip}" if telegram_id is not available (fallback)

    Example:
        "192.168.1.1:123456789" or "192.168.1.1"
    """
    ip = get_remote_address(request)

    try:
        # Extract Authorization header (format: "tma {initData}")
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("tma "):
            return ip

        # Extract initData
        init_data = auth.split(" ", 1)[1]

        # Parse initData (simple parsing, no full HMAC validation needed here)
        params = {}
        for pair in init_data.split('&'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                params[key] = unquote(value)

        # Extract user JSON from initData
        user_json = params.get('user')
        if not user_json:
            return ip

        # Parse user data to get telegram_id
        user_data = json.loads(user_json)
        telegram_id = user_data.get('id')

        if telegram_id:
            return f"{ip}:{telegram_id}"
    except Exception:
        # If anything fails, fall back to IP-only rate limiting
        # This ensures rate limiting still works even if parsing fails
        pass

    return ip


# Create global limiter instance with custom key function
limiter = Limiter(key_func=get_user_identifier)
