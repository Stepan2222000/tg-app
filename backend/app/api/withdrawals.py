# backend/app/api/withdrawals.py
"""
Withdrawal management endpoints.
Handles withdrawal requests and history.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.db.database import db
from app.utils.config import config
from app.utils.datetime import to_iso8601
from app.utils.validation import validate_withdrawal_details

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/")
async def create_withdrawal(
    amount: int = Body(..., embed=True),
    method: str = Body(..., embed=True),
    details: Dict[str, str] = Body(..., embed=True),
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create withdrawal request.

    PROTECTED endpoint - requires valid Telegram initData in Authorization header.

    Request body:
    {
        "amount": 500,              # Amount to withdraw (in rubles)
        "method": "card" | "sbp",   # Withdrawal method
        "details": {                # Method-specific details
            # For 'card':
            "card_number": "1234567890123456",
            "cardholder_name": "IVAN IVANOV"

            # For 'sbp':
            "bank_name": "Sberbank",
            "phone_number": "+79991234567"
        }
    }

    Validation logic:
    1. Validate withdrawal details based on method (via validate_withdrawal_details)
    2. Check amount >= MIN_WITHDRAWAL
    3. Calculate total pending withdrawals
    4. Check: (main_balance + referral_balance) - pending_sum >= amount
    5. Deduct from main_balance first, then referral_balance if needed

    Args:
        amount: Amount to withdraw (in rubles, integer)
        method: Withdrawal method ('card' or 'sbp')
        details: Method-specific withdrawal details
        user: Current user from get_current_user dependency

    Returns:
        Created withdrawal object:
        {
            "id": int,
            "user_id": int,
            "amount": int,
            "method": str,
            "details": dict,
            "status": "pending",
            "created_at": str (ISO 8601),
            "processed_at": null
        }

    Raises:
        400: Invalid withdrawal details, insufficient balance, or amount too low
        500: Database error
    """
    telegram_id = user["telegram_id"]

    # Sanitize details for logging (hide sensitive financial data)
    sanitized_details = details.copy()
    if 'card_number' in sanitized_details and sanitized_details['card_number']:
        # Show only last 4 digits
        card = sanitized_details['card_number'].replace(' ', '')
        sanitized_details['card_number'] = f"****{card[-4:]}" if len(card) >= 4 else "****"
    if 'phone_number' in sanitized_details and sanitized_details['phone_number']:
        phone = sanitized_details['phone_number']
        sanitized_details['phone_number'] = f"****{phone[-4:]}" if len(phone) >= 4 else "****"

    logger.info(
        f"create_withdrawal called for user {telegram_id}: "
        f"amount={amount}, method={method}, details={sanitized_details}"
    )

    # Validate withdrawal details (method + details)
    is_valid, error_message = validate_withdrawal_details(method, details)
    if not is_valid:
        logger.warning(f"Invalid withdrawal details for user {telegram_id}: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # NEW-HIGH-2 FIX: Validate amount (positive, not too large)
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal amount must be positive"
        )

    # Maximum withdrawal: 1 million rubles per request
    MAX_WITHDRAWAL_AMOUNT = 1000000
    if amount > MAX_WITHDRAWAL_AMOUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum withdrawal amount is {MAX_WITHDRAWAL_AMOUNT:,} rubles"
        )

    # Check minimum withdrawal amount
    if amount < config.MIN_WITHDRAWAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum withdrawal amount is {config.MIN_WITHDRAWAL} rubles"
        )

    # Use transaction with FOR UPDATE to prevent race conditions
    # Two concurrent withdrawal requests will be serialized
    try:
        async with db.transaction() as conn:
            # NEW-CRITICAL-7 FIX: Check pending withdrawals count (rate limiting)
            pending_count = await conn.fetchval(
                "SELECT COUNT(*) FROM withdrawals WHERE user_id = $1 AND status = 'pending'",
                telegram_id
            )

            if pending_count >= 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Too many pending withdrawals. Please wait for approval of existing requests (max 5 pending)."
                )

            # NEW-CRITICAL-2 FIX: Lock user row first, then separately lock and sum withdrawals
            # This prevents race condition where two requests see same pending_sum
            user_data = await conn.fetchrow(
                "SELECT main_balance, referral_balance FROM users WHERE telegram_id = $1 FOR UPDATE",
                telegram_id
            )

            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Lock pending withdrawals and calculate sum
            pending_sum = await conn.fetchval(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM withdrawals
                WHERE user_id = $1 AND status = 'pending'
                FOR UPDATE
                """,
                telegram_id
            ) or 0

            main_balance = user_data['main_balance']
            referral_balance = user_data['referral_balance']

            total_balance = main_balance + referral_balance
            available_balance = total_balance - pending_sum

            # Check if user has enough available balance
            if available_balance < amount:
                logger.warning(
                    f"Insufficient balance for user {telegram_id}: "
                    f"total={total_balance}, pending={pending_sum}, available={available_balance}, requested={amount}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient balance. Available: {available_balance} rubles (pending withdrawals: {pending_sum})"
                )

            # Create withdrawal request with status='pending'
            # Balance is not deducted yet - will be deducted by admin on approval
            # The pending status acts as a "soft reservation"
            withdrawal = await conn.fetchrow(
                """
                INSERT INTO withdrawals (user_id, amount, method, details, status)
                VALUES ($1, $2, $3, $4, 'pending')
                RETURNING *
                """,
                telegram_id,
                amount,
                method,
                details  # PostgreSQL will convert dict to JSONB
            )

            logger.info(
                f"Created withdrawal request {withdrawal['id']} for user {telegram_id} "
                f"(amount={amount}, method={method})"
            )

        # Convert datetime to ISO 8601
        withdrawal_response = dict(withdrawal)
        if withdrawal_response.get("created_at"):
            withdrawal_response["created_at"] = to_iso8601(withdrawal_response["created_at"])
        if withdrawal_response.get("processed_at"):
            withdrawal_response["processed_at"] = to_iso8601(withdrawal_response["processed_at"])

        return withdrawal_response

    except HTTPException:
        # Re-raise HTTPException
        raise
    except Exception as e:
        logger.error(f"Failed to create withdrawal for user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create withdrawal request"
        )


@router.get("/history")
async def get_withdrawal_history(
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get withdrawal history for current user.

    PROTECTED endpoint - requires valid Telegram initData in Authorization header.

    Returns all withdrawal requests for the current user, sorted by created_at DESC (newest first).

    Args:
        user: Current user from get_current_user dependency

    Returns:
        List of withdrawal objects:
        [
            {
                "id": int,
                "user_id": int,
                "amount": int,
                "method": "card" | "sbp",
                "details": dict,
                "status": "pending" | "approved" | "rejected",
                "created_at": str (ISO 8601),
                "processed_at": str (ISO 8601) | null
            },
            ...
        ]

    Raises:
        500: Database error
    """
    telegram_id = user["telegram_id"]

    logger.info(f"get_withdrawal_history called for user {telegram_id}")

    try:
        # Get all withdrawals for user, sorted by created_at DESC
        withdrawals = await db.fetch_all(
            """
            SELECT *
            FROM withdrawals
            WHERE user_id = $1
            ORDER BY created_at DESC
            """,
            telegram_id
        )

        # Convert to list of dicts with ISO 8601 timestamps
        result = []
        for withdrawal in withdrawals:
            withdrawal_dict = dict(withdrawal)
            if withdrawal_dict.get("created_at"):
                withdrawal_dict["created_at"] = to_iso8601(withdrawal_dict["created_at"])
            if withdrawal_dict.get("processed_at"):
                withdrawal_dict["processed_at"] = to_iso8601(withdrawal_dict["processed_at"])
            result.append(withdrawal_dict)

        logger.info(f"Returning {len(result)} withdrawals for user {telegram_id}")
        return result

    except Exception as e:
        logger.error(f"Failed to fetch withdrawal history for user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch withdrawal history"
        )
