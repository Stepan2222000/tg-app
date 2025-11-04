# backend/app/utils/validation.py
"""
Validation utilities for user input.
Handles phone numbers, card numbers, and withdrawal details validation.
"""

import re
from typing import Optional, Dict, Tuple


def validate_phone_number(phone: str) -> bool:
    """
    Validate Russian phone number format.

    Args:
        phone: Phone number string

    Returns:
        True if valid, False otherwise

    Examples:
        validate_phone_number("+79991234567") -> True
        validate_phone_number("+7 999 123 45 67") -> False (spaces not allowed)
        validate_phone_number("89991234567") -> False (must start with +7)
        validate_phone_number("+79991234") -> False (too short)
    """
    pattern = r'^\+7\d{10}$'
    return bool(re.match(pattern, phone))


def validate_card_number(card: str) -> bool:
    """
    Validate card number (16 digits, spaces allowed).

    Args:
        card: Card number string (may contain spaces)

    Returns:
        True if valid, False otherwise

    Examples:
        validate_card_number("1234567890123456") -> True
        validate_card_number("1234 5678 9012 3456") -> True
        validate_card_number("1234567890") -> False (too short)
        validate_card_number("abcd567890123456") -> False (contains letters)
    """
    # Remove spaces
    card_clean = card.replace(' ', '')
    # Check if 16 digits
    pattern = r'^\d{16}$'
    return bool(re.match(pattern, card_clean))


def normalize_card_number(card: str) -> str:
    """
    Remove spaces from card number.

    Args:
        card: Card number string (may contain spaces)

    Returns:
        Card number without spaces

    Example:
        normalize_card_number("1234 5678 9012 3456") -> "1234567890123456"
    """
    return card.replace(' ', '')


def validate_withdrawal_details(method: str, details: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Validate withdrawal details based on method.

    For 'card' method, requires:
        - card_number: 16 digits (spaces allowed)
        - cardholder_name: non-empty string

    For 'sbp' method, requires:
        - bank_name: non-empty string
        - phone_number: Russian format +7XXXXXXXXXX

    Args:
        method: Withdrawal method ('card' or 'sbp')
        details: Details dictionary

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])

    Examples:
        validate_withdrawal_details('card', {...}) -> (True, None)
        validate_withdrawal_details('card', {}) -> (False, "Missing required fields for card withdrawal")
        validate_withdrawal_details('invalid', {}) -> (False, "Unknown withdrawal method: invalid")
    """
    if method == 'card':
        # Check required fields
        if 'card_number' not in details or 'cardholder_name' not in details:
            return False, "Missing required fields: card_number and cardholder_name"

        # Validate and normalize card number
        card_number = normalize_card_number(details['card_number'])
        if not validate_card_number(card_number):
            return False, "Invalid card number format (must be 16 digits)"

        # Validate cardholder name
        if not details['cardholder_name'].strip():
            return False, "Cardholder name cannot be empty"

        # Normalize card number in details (remove spaces)
        details['card_number'] = card_number

    elif method == 'sbp':
        # Check required fields
        if 'bank_name' not in details or 'phone_number' not in details:
            return False, "Missing required fields: bank_name and phone_number"

        # Validate phone number
        if not validate_phone_number(details['phone_number']):
            return False, "Invalid phone number format (must be +7XXXXXXXXXX)"

        # Validate bank name
        if not details['bank_name'].strip():
            return False, "Bank name cannot be empty"

    else:
        return False, f"Unknown withdrawal method: {method}"

    return True, None
