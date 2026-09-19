import os
import sys
import logging
import threading
import traceback

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Flask app for Render
flask_app = Flask(__name__)


@flask_app.route("/")
def home():
    return "Reward Bot is running!"


def run_flask():
    port = int(os.environ.get("PORT", "10000"))
    flask_app.run(
        host="0.0.0.0",
        port=port,
        use_reloader=False
    )


# Telegram /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Welcome to Reward Bot.\n\n"
        "Use /help to see available commands."
    )


# Telegram /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show help"
    )


def main():
    # Start Flask server
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )
    flask_thread.start()

    # Get Telegram Bot Token
    bot_token = os.environ.get("BOT_TOKEN")

    if not bot_token:
        print("ERROR: BOT_TOKEN is missing from Render Environment Variables.")
        sys.exit(1)

    bot_token = bot_token.strip()

    print("BOT_TOKEN found.")
    print("Starting Telegram bot...")

    try:
        # Create Telegram application
        application = (
            Application.builder()
            .token(bot_token)
            .build()
        )

        # Commands
        application.add_handler(
            CommandHandler("start", start)
        )

        application.add_handler(
            CommandHandler("help", help_command)
        )

        print("Bot is starting polling...")

        # Start bot
        application.run_polling(
            drop_pending_updates=True
        )

    except Exception as error:
        print("====================================")
        print("BOT STARTUP ERROR")
        print("====================================")
        print(str(error))
        traceback.print_exc()
        print("====================================")

        sys.exit(1)


if __name__ == "__main__":
    main()
