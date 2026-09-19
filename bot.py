import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Initialize Flask application for Render health checks
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    """Health check endpoint required by Render Web Service."""
    return 'Telegram Bot is running!'

def run_flask():
    """Runs the Flask web server on 0.0.0.0 and port from environment variable."""
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port)

# Telegram Bot Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    await update.message.reply_text(
        "👋 Welcome to Reward Bot! 🤖\nYour Telegram bot is working successfully! ✅"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command."""
    await update.message.reply_text(
        "/start - Start the bot\n/help - Show help\n/about - About the bot"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /about command."""
    await update.message.reply_text(
        "Reward Bot is a simple, lightweight Telegram bot designed to distribute rewards, notifications, and manage interactive community tasks on Telegram."
    )

def main():
    """Main application entry point."""
    # Retrieve Telegram Bot Token from environment variable
    token = os.environ.get('BOT_TOKEN')
    if not token:
        print("ERROR: BOT_TOKEN environment variable is not set.")
        print("Please configure BOT_TOKEN in your Render Environment Variables.")
        exit(1)

    # Start Flask in a background daemon thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Flask server started in background thread.")

    # Initialize and start python-telegram-bot application with Long Polling
    application = ApplicationBuilder().token(token).build()

    # Register command handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('about', about_command))

    print("Reward Bot started with long polling (Webhooks are disabled).")
    # Run long polling
    application.run_polling()

if __name__ == '__main__':
    main()