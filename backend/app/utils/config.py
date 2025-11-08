# backend/app/utils/config.py
"""
Utility functions for reading and parsing environment variables.
Handles type conversion from string to int/float.
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory
# Find .env in the backend directory (parent of app/)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def get_int_env(key: str, default: Optional[int] = None) -> int:
    """
    Get integer environment variable.

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Integer value

    Raises:
        ValueError: If value cannot be converted to int
        KeyError: If key not found and no default provided

    Example:
        max_file_size = get_int_env('MAX_FILE_SIZE', 10485760)
    """
    value = os.getenv(key)
    if value is None:
        if default is not None:
            return default
        raise KeyError(f"Environment variable '{key}' not found and no default provided")
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Environment variable '{key}' value '{value}' cannot be converted to int")


def get_float_env(key: str, default: Optional[float] = None) -> float:
    """
    Get float environment variable.

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Float value

    Raises:
        ValueError: If value cannot be converted to float
        KeyError: If key not found and no default provided

    Example:
        commission = get_float_env('REFERRAL_COMMISSION', 0.5)
    """
    value = os.getenv(key)
    if value is None:
        if default is not None:
            return default
        raise KeyError(f"Environment variable '{key}' not found and no default provided")
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Environment variable '{key}' value '{value}' cannot be converted to float")


def get_str_env(key: str, default: Optional[str] = None) -> str:
    """
    Get string environment variable.

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        String value

    Raises:
        KeyError: If key not found and no default provided

    Example:
        bot_token = get_str_env('TELEGRAM_BOT_TOKEN')
    """
    value = os.getenv(key)
    if value is None:
        if default is not None:
            return default
        raise KeyError(f"Environment variable '{key}' not found and no default provided")
    return value


def get_bool_env(key: str, default: Optional[bool] = None) -> bool:
    """
    Get boolean environment variable.
    Accepts: true/false, yes/no, 1/0 (case insensitive)

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Boolean value

    Raises:
        ValueError: If value cannot be converted to bool
        KeyError: If key not found and no default provided

    Example:
        debug = get_bool_env('DEBUG', False)
    """
    value = os.getenv(key)
    if value is None:
        if default is not None:
            return default
        raise KeyError(f"Environment variable '{key}' not found and no default provided")

    value_lower = value.lower()
    if value_lower in ('true', 'yes', '1'):
        return True
    elif value_lower in ('false', 'no', '0'):
        return False
    else:
        raise ValueError(
            f"Environment variable '{key}' value '{value}' cannot be converted to bool. "
            f"Use: true/false, yes/no, 1/0"
        )


# Pre-loaded configuration values for easy access
class Config:
    """Application configuration loaded from environment variables."""

    # Database
    DATABASE_HOST: str = get_str_env('DATABASE_HOST')
    DATABASE_PORT: int = get_int_env('DATABASE_PORT')
    DATABASE_NAME: str = get_str_env('DATABASE_NAME')
    DATABASE_USER: str = get_str_env('DATABASE_USER')
    DATABASE_PASSWORD: str = get_str_env('DATABASE_PASSWORD')

    # Telegram
    TELEGRAM_BOT_TOKEN: str = get_str_env('TELEGRAM_BOT_TOKEN')
    TELEGRAM_BOT_USERNAME: str = get_str_env('TELEGRAM_BOT_USERNAME')
    TELEGRAM_APP_SHORT_NAME: str = get_str_env('TELEGRAM_APP_SHORT_NAME', 'avitotasker')

    # File Upload
    UPLOAD_DIR: str = get_str_env('UPLOAD_DIR', './uploads/screenshots')
    MAX_FILE_SIZE: int = get_int_env('MAX_FILE_SIZE', 10485760)  # 10MB default

    # Pricing & Limits
    SIMPLE_TASK_PRICE: int = get_int_env('SIMPLE_TASK_PRICE', 50)
    PHONE_TASK_PRICE: int = get_int_env('PHONE_TASK_PRICE', 150)
    REFERRAL_COMMISSION: float = get_float_env('REFERRAL_COMMISSION', 0.5)
    MIN_WITHDRAWAL: int = get_int_env('MIN_WITHDRAWAL', 100)
    MAX_ACTIVE_TASKS: int = get_int_env('MAX_ACTIVE_TASKS', 10)
    TASK_LOCK_HOURS: int = get_int_env('TASK_LOCK_HOURS', 24)

    # General
    GENERAL_INSTRUCTION: str = get_str_env('GENERAL_INSTRUCTION', '')
    ENVIRONMENT: str = get_str_env('ENVIRONMENT', 'development')


# Export singleton instance
config = Config()
