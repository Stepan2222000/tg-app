"""Bot command handlers."""
import logging
import re
from telegram import Update
from telegram.ext import ContextTypes

from app.db.database import db
from app.bot.keyboards import get_welcome_keyboard
from app.dependencies.auth import hash_user_id
from app.utils.config import config

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command with optional referral code.

    Format: /start ref_TELEGRAM_ID

    Logic:
    1. Extract telegram_id, username, first_name from message
    2. Parse referral code from args (if present)
    3. Validate referral code (referrer exists, not self-referral)
    4. Insert/update user in DB with referred_by (only if NULL)
    5. Send welcome message with Mini App button
    """
    user = update.effective_user
    if not user:
        logger.warning("No user in update.effective_user")
        return

    telegram_id = user.id
    username = user.username
    first_name = user.first_name or ""

    logger.info(f"Bot: /start command from user {hash_user_id(telegram_id)} (@{username or 'no_username'})")

    # Parse referral code from /start argument
    referred_by = None
    if context.args and len(context.args) > 0:
        ref_arg = context.args[0]
        # Format: ref_TELEGRAM_ID
        match = re.match(r'^ref_(\d+)$', ref_arg)
        if match:
            try:
                referred_by = int(match.group(1))
                logger.info(f"Bot: Referral code detected - {hash_user_id(referred_by)}")
            except ValueError:
                logger.warning(f"Bot: Invalid referral code format: {ref_arg}")
                referred_by = None

    # Validate referral code
    if referred_by:
        # Check self-referral
        if referred_by == telegram_id:
            logger.warning(f"Bot: Self-referral attempt blocked - {hash_user_id(telegram_id)}")
            referred_by = None
        else:
            # Check referrer exists
            try:
                referrer = await db.fetch_one(
                    "SELECT telegram_id FROM users WHERE telegram_id = $1",
                    referred_by
                )
                if not referrer:
                    logger.warning(f"Bot: Referrer not found - {hash_user_id(referred_by)}")
                    referred_by = None
                else:
                    logger.info(f"Bot: Valid referral - {hash_user_id(telegram_id)} referred by {hash_user_id(referred_by)}")
            except Exception as e:
                logger.error(f"Bot: Failed to check referrer {hash_user_id(referred_by)}: {e}")
                referred_by = None

    # Insert or update user with referred_by (only if NULL)
    try:
        await db.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, referred_by)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (telegram_id) DO UPDATE
            SET username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                referred_by = EXCLUDED.referred_by
            WHERE users.referred_by IS NULL
            """,
            telegram_id,
            username,
            first_name,
            referred_by
        )
        logger.info(
            f"Bot: User upserted - {hash_user_id(telegram_id)}, "
            f"referred_by={'none' if referred_by is None else hash_user_id(referred_by)}"
        )
    except Exception as e:
        logger.error(f"Bot: Failed to insert/update user {hash_user_id(telegram_id)}: {e}", exc_info=True)
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
        return

    # Send welcome message with Mini App button
    commission_percent = int(config.REFERRAL_COMMISSION * 100)
    welcome_text = (
        f"Привет, {first_name}! 👋\n\n"
        "Добро пожаловать в Avito Tasker - платформу для заработка на простых задачах.\n\n"
        f"💰 СВЕРХВЫГОДНЫЕ условия:\n"
        f"• Простая задача: {config.SIMPLE_TASK_PRICE}₽\n"
        f"• Задача с номером телефона: {config.PHONE_TASK_PRICE}₽\n\n"
        f"🎁 РЕФЕРАЛЬНАЯ ПРОГРАММА:\n"
        f"Приглашай друзей и получай {commission_percent}% от КАЖДОГО их заработка!\n"
        f"Это значит, что твои рефералы зарабатывают столько же, а ты получаешь дополнительный доход!\n\n"
        "Зарабатывай, отправляя несколько сообщений в день в Avito - простая работа, щедрая оплата!\n\n"
        "Нажми кнопку ниже, чтобы начать:"
    )

    try:
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_welcome_keyboard()
        )
        logger.info(f"Bot: Welcome message sent to {hash_user_id(telegram_id)}")
    except Exception as e:
        logger.error(f"Bot: Failed to send welcome message to {hash_user_id(telegram_id)}: {e}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    commission_percent = int(config.REFERRAL_COMMISSION * 100)
    help_text = (
        "Avito Tasker - зарабатывай на выполнении простых задач!\n\n"
        f"💰 Цены:\n"
        f"• Простая задача: {config.SIMPLE_TASK_PRICE}₽\n"
        f"• Задача с номером телефона: {config.PHONE_TASK_PRICE}₽\n\n"
        f"🎁 Реферальная программа:\n"
        f"Приглашай друзей и получай {commission_percent}% от их заработка!\n\n"
        "Используй /start для открытия приложения."
    )
    try:
        await update.message.reply_text(help_text)
    except Exception as e:
        logger.error(f"Bot: Failed to send help message: {e}")
