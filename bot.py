import os
import asyncio
import threading
import logging
import traceback

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

app = Flask(__name__)


@app.route("/")
def home():
    return "Reward Bot is running!"


def run_flask():
    port = int(os.environ.get("PORT", "10000"))
    app.run(
        host="0.0.0.0",
        port=port,
        use_reloader=False
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Welcome to Reward Bot!\n\n"
        "Use /help to see available commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show help"
    )


async def run_bot():
    token = os.environ.get("BOT_TOKEN")

    if not token:
        print("ERROR: BOT_TOKEN is missing.")
        return

    token = token.strip()

    print("BOT_TOKEN found.")
    print("Creating Telegram application...")

    application = (
        Application.builder()
        .token(token)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    try:
        print("Initializing bot...")

        await application.initialize()

        print("Starting bot...")
        await application.start()

        print("Starting Telegram polling...")

        await application.updater.start_polling(
            drop_pending_updates=True
        )

        print("BOT IS RUNNING SUCCESSFULLY!")

        # Keep the bot running
        await asyncio.Event().wait()

    except Exception as error:
        print("====================================")
        print("BOT STARTUP ERROR")
        print("====================================")
        print(str(error))
        traceback.print_exc()
        print("====================================")

    finally:
        try:
            if application.updater:
                await application.updater.stop()

            await application.stop()
            await application.shutdown()

        except Exception:
            pass


def main():
    print("Starting Reward Bot...")

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
