"""Bot initialization and run."""
import logging
from telegram.ext import Application, CommandHandler

from app.utils.config import config
from app.db.database import db
from app.bot.handlers import start_command, help_command

logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """
    Called after bot is initialized.
    Initialize database connection here.
    """
    await db.connect()
    logger.info("Bot: Database pool initialized")


async def post_stop(application: Application) -> None:
    """
    Called after bot stops.
    Close database connection here.
    """
    await db.disconnect()
    logger.info("Bot: Database pool closed")


def run_bot():
    """
    Run bot with polling.

    Initializes database connection, creates bot application,
    and starts polling for updates.

    This is a blocking call - it will run until stopped.
    """
    logger.info("Starting Telegram bot...")

    # Create application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    logger.info("Bot handlers registered")

    # Add lifecycle hooks
    application.post_init = post_init
    application.post_stop = post_stop

    # Run bot (blocking call)
    logger.info("Bot: Starting polling...")
    application.run_polling(allowed_updates=["message"])
