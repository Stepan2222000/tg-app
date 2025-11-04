# backend/app/api/referrals.py
"""
Referral program endpoints.
Handles referral link generation, statistics, and detailed referral lists.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
import logging

from app.dependencies.auth import get_current_user
from app.db.database import db
from app.utils.config import config

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/link")
async def get_referral_link(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, str]:
    """
    Generate referral link for current user.

    PROTECTED endpoint - requires valid Telegram initData in Authorization header.

    Returns:
        {"link": "https://t.me/bot_username?start=ref_TELEGRAM_ID"}

    Example:
        GET /api/referrals/link
        Response: {"link": "https://t.me/avito_tasker_bot?start=ref_123456789"}
    """
    telegram_id = user['telegram_id']
    bot_username = config.TELEGRAM_BOT_USERNAME

    # Format: https://t.me/{bot_username}?start=ref_{telegram_id}
    referral_link = f"https://t.me/{bot_username}?start=ref_{telegram_id}"

    logger.info(f"Generated referral link for user {telegram_id}")

    return {"link": referral_link}


@router.get("/stats")
async def get_referral_stats(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get referral statistics (count and total earnings).

    PROTECTED endpoint - requires valid Telegram initData in Authorization header.

    Returns:
        {
            "total_referrals": int,  # Number of users referred
            "total_earnings": int    # Total commission earned in rubles
        }

    Example:
        GET /api/referrals/stats
        Response: {"total_referrals": 12, "total_earnings": 1250}
    """
    telegram_id = user['telegram_id']

    # Count total referrals (users who have this user as referrer)
    referral_count_result = await db.fetch_one(
        """
        SELECT COUNT(*) as count
        FROM users
        WHERE referred_by = $1
        """,
        telegram_id
    )
    total_referrals = referral_count_result['count'] if referral_count_result else 0

    # Sum total earnings from referral_earnings table
    earnings_result = await db.fetch_one(
        """
        SELECT COALESCE(SUM(amount), 0) as total
        FROM referral_earnings
        WHERE referrer_id = $1
        """,
        telegram_id
    )
    total_earnings = int(earnings_result['total']) if earnings_result else 0

    logger.info(f"Fetched referral stats for user {telegram_id}: {total_referrals} referrals, {total_earnings}₽")

    return {
        "total_referrals": total_referrals,
        "total_earnings": total_earnings
    }


@router.get("/list")
async def get_referral_list(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get detailed referral list with earnings breakdown.

    PROTECTED endpoint - requires valid Telegram initData in Authorization header.

    Returns:
        {
            "total_referrals": int,
            "total_earnings": int,
            "referrals": [
                {
                    "telegram_id": int,
                    "username": str | null,
                    "simple_tasks": int,    # Number of simple tasks completed
                    "phone_tasks": int,     # Number of phone tasks completed
                    "earnings": int         # Total commission from this referral
                }
            ]
        }

    Example:
        GET /api/referrals/list
        Response: {
            "total_referrals": 2,
            "total_earnings": 150,
            "referrals": [
                {
                    "telegram_id": 123456,
                    "username": "user123",
                    "simple_tasks": 2,
                    "phone_tasks": 1,
                    "earnings": 100
                },
                {
                    "telegram_id": 789012,
                    "username": null,
                    "simple_tasks": 1,
                    "phone_tasks": 0,
                    "earnings": 50
                }
            ]
        }
    """
    telegram_id = user['telegram_id']

    # Get referrals with aggregated task counts and earnings
    # We need to join users with referral_earnings and count by task_type
    referrals_data = await db.fetch_all(
        """
        SELECT
            u.telegram_id,
            u.username,
            COALESCE(SUM(CASE WHEN re.task_type = 'simple' THEN 1 ELSE 0 END), 0) as simple_tasks,
            COALESCE(SUM(CASE WHEN re.task_type = 'phone' THEN 1 ELSE 0 END), 0) as phone_tasks,
            COALESCE(SUM(re.amount), 0) as earnings
        FROM users u
        LEFT JOIN referral_earnings re ON re.referral_id = u.telegram_id
        WHERE u.referred_by = $1
        GROUP BY u.telegram_id, u.username
        ORDER BY earnings DESC
        """,
        telegram_id
    )

    # Convert to list of dicts with proper types
    referrals_list: List[Dict[str, Any]] = []
    total_referrals = 0
    total_earnings = 0

    for row in referrals_data:
        referral = {
            "telegram_id": row['telegram_id'],
            "username": row['username'],
            "simple_tasks": int(row['simple_tasks']),
            "phone_tasks": int(row['phone_tasks']),
            "earnings": int(row['earnings'])
        }
        referrals_list.append(referral)
        total_referrals += 1
        total_earnings += referral['earnings']

    logger.info(f"Fetched referral list for user {telegram_id}: {total_referrals} referrals")

    return {
        "total_referrals": total_referrals,
        "total_earnings": total_earnings,
        "referrals": referrals_list
    }
