#!/usr/bin/env python3
"""
Telegram Bot для Avito Tasker Mini App
Обрабатывает команду /start и открывает Mini App через inline кнопку
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение переменных окружения
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MINI_APP_URL = os.getenv("MINI_APP_URL")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

if not MINI_APP_URL:
    raise ValueError("MINI_APP_URL not found in environment variables")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start
    Отправляет приветственное сообщение с кнопкой для запуска Mini App
    """
    user = update.effective_user
    logger.info(f"User {user.id} (@{user.username}) started the bot")
    logger.info(f"Sending Mini App URL: {MINI_APP_URL}")

    # Создание inline кнопки с WebApp
    keyboard = [
        [
            InlineKeyboardButton(
                text="🚀 Открыть Avito Tasker",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Приветственное сообщение
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "🎯 Добро пожаловать в **Avito Tasker** - заработай деньги, "
        "выполняя простые задания на Avito!\n\n"
        "💰 **Что можно делать:**\n"
        "• Выполнять простые задания (50₽)\n"
        "• Выполнять задания с телефоном (150₽)\n"
        "• Приглашать друзей и получать бонусы\n"
        "• Выводить деньги на карту или СБП\n\n"
        "👇 Нажми на кнопку ниже, чтобы начать!"
    )

    await update.message.reply_text(
        text=welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик ошибок
    """
    logger.error(f"Update {update} caused error {context.error}")


def main() -> None:
    """
    Запуск бота
    """
    logger.info("Starting Avito Tasker Bot...")
    logger.info(f"Bot Token: {BOT_TOKEN[:10]}...")
    logger.info(f"Mini App URL: {MINI_APP_URL}")

    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start_command))
    application.add_error_handler(error_handler)

    # Запуск бота
    logger.info("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
