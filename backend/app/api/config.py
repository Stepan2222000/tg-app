# backend/app/api/config.py
"""
Configuration endpoints.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter

from app.utils.config import config

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
