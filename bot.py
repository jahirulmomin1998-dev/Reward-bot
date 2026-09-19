import os
import asyncio
import threading
import logging
import traceback

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

app = Flask(__name__)

# Temporary coin storage
# Database will be added in the next step.
user_coins = {}


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


def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("🎁 Earn Coins", callback_data="earn")
        ],
        [
            InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_coins:
        user_coins[user_id] = 0

    await update.message.reply_text(
        "🎉 Welcome to Reward Bot!\n\n"
        "💰 Earn coins and use them for rewards.\n\n"
        "Choose an option below:",
        reply_markup=main_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in user_coins:
        user_coins[user_id] = 0

    if query.data == "balance":
        coins = user_coins[user_id]

        await query.edit_message_text(
            f"💰 Your Balance\n\n"
            f"🪙 Coins: {coins}\n\n"
            f"Keep earning to increase your balance!",
            reply_markup=main_menu()
        )

    elif query.data == "earn":
        user_coins[user_id] += 10
        coins = user_coins[user_id]

        await query.edit_message_text(
            f"🎁 Reward Received!\n\n"
            f"🪙 +10 Coins\n"
            f"💰 Total Balance: {coins} Coins",
            reply_markup=main_menu()
        )

    elif query.data == "withdraw":
        coins = user_coins[user_id]

        await query.edit_message_text(
            f"💸 Withdraw\n\n"
            f"🪙 Your Balance: {coins} Coins\n\n"
            f"Withdrawal system will be added in the next step.",
            reply_markup=main_menu()
        )

    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ Help\n\n"
            "💰 Balance - Check your coins\n"
            "🎁 Earn Coins - Earn reward coins\n"
            "💸 Withdraw - Withdraw your rewards\n\n"
            "More features are coming soon!",
            reply_markup=main_menu()
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Choose an option:",
        reply_markup=main_menu()
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

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    try:
        print("Initializing bot...")

        await application.initialize()
        await application.start()

        print("Starting Telegram polling...")

        await application.updater.start_polling(
            drop_pending_updates=True
        )

        print("BOT IS RUNNING SUCCESSFULLY!")

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
