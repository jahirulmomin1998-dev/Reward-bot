import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Initialize Flask app
flask_app = Flask(__name__)


@flask_app.route("/")
def home():
    return "Reward Bot is running!"


def run_flask():
    # Use the Render PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    # Flask must listen on 0.0.0.0
    flask_app.run(host="0.0.0.0", port=port)


# Telegram command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    await update.message.reply_text("Hello! Welcome to Reward Bot. Use /help to see available commands.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /help command."""
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start interacting with the bot\n"
        "/help - Show help information"
    )


def main():
    # Start Flask in a separate thread so it doesn't block Telegram long polling
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Read the token only from the BOT_TOKEN environment variable
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        print("BOT_TOKEN environment variable is not set. Please configure BOT_TOKEN.")
        return

    # Build the Telegram Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add /start and /help command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Run Telegram long polling
    application.run_polling()


if __name__ == "__main__":
    main()
