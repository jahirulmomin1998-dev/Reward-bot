import os
import asyncio
import threading
import logging
import traceback
import sqlite3

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

DB_FILE = "reward_bot.db"


# =========================
# DATABASE
# =========================

def init_database():
    connection = sqlite3.connect(DB_FILE)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 0
        )
    """)

    connection.commit()
    connection.close()


def get_user(user_id, username=""):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT user_id, username, coins FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users (user_id, username, coins) VALUES (?, ?, ?)",
            (user_id, username, 0)
        )
        connection.commit()

        coins = 0
    else:
        coins = user[2]

    connection.close()

    return coins


def add_coins(user_id, username, amount):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users (user_id, username, coins) VALUES (?, ?, ?)",
            (user_id, username, amount)
        )
    else:
        cursor.execute(
            """
            UPDATE users
            SET coins = coins + ?, username = ?
            WHERE user_id = ?
            """,
            (amount, username, user_id)
        )

    connection.commit()

    cursor.execute(
        "SELECT coins FROM users WHERE user_id = ?",
        (user_id,)
    )

    coins = cursor.fetchone()[0]

    connection.close()

    return coins


# =========================
# FLASK
# =========================

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


# =========================
# MENU
# =========================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "💰 Balance",
                callback_data="balance"
            ),
            InlineKeyboardButton(
                "🎁 Earn Coins",
                callback_data="earn"
            )
        ],
        [
            InlineKeyboardButton(
                "💸 Withdraw",
                callback_data="withdraw"
            ),
            InlineKeyboardButton(
                "ℹ️ Help",
                callback_data="help"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    username = update.effective_user.username or ""

    get_user(user_id, username)

    await update.message.reply_text(
        "🎉 Welcome to Reward Bot!\n\n"
        "💰 Earn coins and use them for rewards.\n\n"
        "Choose an option below:",
        reply_markup=main_menu()
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username or ""

    get_user(user_id, username)

    # BALANCE
    if query.data == "balance":

        coins = get_user(user_id, username)

        await query.edit_message_text(
            f"💰 Your Balance\n\n"
            f"🪙 Coins: {coins}\n\n"
            f"Keep earning to increase your balance!",
            reply_markup=main_menu()
        )

    # EARN
    elif query.data == "earn":

        coins = add_coins(
            user_id,
            username,
            10
        )

        await query.edit_message_text(
            f"🎁 Reward Received!\n\n"
            f"🪙 +10 Coins\n"
            f"💰 Total Balance: {coins} Coins",
            reply_markup=main_menu()
        )

    # WITHDRAW
    elif query.data == "withdraw":

        coins = get_user(user_id, username)

        await query.edit_message_text(
            f"💸 Withdraw\n\n"
            f"🪙 Your Balance: {coins} Coins\n\n"
            f"Withdrawal system will be added next.",
            reply_markup=main_menu()
        )

    # HELP
    elif query.data == "help":

        await query.edit_message_text(
            "ℹ️ Help\n\n"
            "💰 Balance - Check your coins\n"
            "🎁 Earn Coins - Earn reward coins\n"
            "💸 Withdraw - Withdraw your rewards\n\n"
            "More features are coming soon!",
            reply_markup=main_menu()
        )


# =========================
# HELP COMMAND
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "Choose an option:",
        reply_markup=main_menu()
    )


# =========================
# TELEGRAM BOT
# =========================

async def run_bot():

    token = os.environ.get("BOT_TOKEN")

    if not token:

        print("ERROR: BOT_TOKEN is missing.")

        return

    token = token.strip()

    print("BOT_TOKEN found.")

    init_database()

    print("Database initialized.")

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


# =========================
# MAIN
# =========================

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
