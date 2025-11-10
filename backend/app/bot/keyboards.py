"""Inline keyboards for bot."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from app.utils.config import config


def get_welcome_keyboard() -> InlineKeyboardMarkup:
    """
    Create welcome keyboard with Mini App button.

    Returns:
        InlineKeyboardMarkup with Web App button to open Mini App
    """
    # For WebAppInfo, we need the direct HTTPS URL of the Mini App
    # NOT a t.me/bot/app link (that format is only for Direct Links)
    # The Mini App URL should point to the actual web application
    mini_app_url = config.MINI_APP_URL

    keyboard = [
        [
            InlineKeyboardButton(
                text="🚀 Открыть приложение",
                web_app=WebAppInfo(url=mini_app_url)
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
