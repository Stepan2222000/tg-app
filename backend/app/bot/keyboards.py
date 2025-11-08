"""Inline keyboards for bot."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from app.utils.config import config


def get_welcome_keyboard() -> InlineKeyboardMarkup:
    """
    Create welcome keyboard with Mini App button.

    Returns:
        InlineKeyboardMarkup with Web App button to open Mini App
    """
    # Generate Mini App URL from config
    mini_app_url = f"https://t.me/{config.TELEGRAM_BOT_USERNAME}/{config.TELEGRAM_APP_SHORT_NAME}"

    keyboard = [
        [
            InlineKeyboardButton(
                text="🚀 Открыть приложение",
                web_app=WebAppInfo(url=mini_app_url)
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
