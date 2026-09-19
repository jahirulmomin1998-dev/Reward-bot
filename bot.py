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

# Demo video
VIDEO_URL = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"

VIDEO_ID = "video_1"
REWARD_COINS = 10
WATCH_SECONDS = 10

# Prevent multiple rewards while the same video is being watched
pending_videos = set()


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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watched_videos (
            user_id INTEGER,
            video_id TEXT,
            watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, video_id)
        )
    """)

    connection.commit()
    connection.close()


def get_user(user_id, username=""):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT coins FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            """
            INSERT INTO users (user_id, username, coins)
            VALUES (?, ?, ?)
            """,
            (user_id, username, 0)
        )

        connection.commit()
        coins = 0
    else:
        coins = user[0]

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
            """
            INSERT INTO users (user_id, username, coins)
            VALUES (?, ?, ?)
            """,
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


def already_watched(user_id, video_id):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM watched_videos
        WHERE user_id = ? AND video_id = ?
        """,
        (user_id, video_id)
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None


def mark_video_watched(user_id, video_id):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO watched_videos
        (user_id, video_id)
        VALUES (?, ?)
        """,
        (user_id, video_id)
    )

    connection.commit()

    inserted = cursor.rowcount

    connection.close()

    return inserted == 1


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
# MAIN MENU
# =========================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "🎬 Watch Video",
                callback_data="watch_video"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 Balance",
                callback_data="balance"
            ),
            InlineKeyboardButton(
                "💸 Withdraw",
                callback_data="withdraw"
            )
        ],
        [
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
        "🎬 Watch videos and earn coins.\n"
        "🪙 Reward: 10 Coins per video.\n\n"
        "Choose an option:",
        reply_markup=main_menu()
    )


# =========================
# GIVE VIDEO REWARD
# =========================

async def reward_after_watch(
    bot,
    chat_id,
    user_id,
    username
):

    try:

        await asyncio.sleep(WATCH_SECONDS)

        # Check again
        if already_watched(user_id, VIDEO_ID):
            return

        # Mark first
        reward_allowed = mark_video_watched(
            user_id,
            VIDEO_ID
        )

        if not reward_allowed:
            return

        coins = add_coins(
            user_id,
            username,
            REWARD_COINS
        )

        await bot.send_message(
            chat_id=chat_id,
            text=(
                "🎉 Video Reward!\n\n"
                f"🪙 +{REWARD_COINS} Coins\n"
                f"💰 Total Balance: {coins} Coins"
            ),
            reply_markup=main_menu()
        )

    except Exception as error:

        print("REWARD ERROR:")
        print(str(error))

    finally:

        pending_videos.discard(
            (user_id, VIDEO_ID)
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

    # WATCH VIDEO
    if query.data == "watch_video":

        if already_watched(user_id, VIDEO_ID):

            await query.edit_message_text(
                "✅ You already earned the reward "
                "for this video.\n\n"
                "🎬 New videos will be added soon.",
                reply_markup=main_menu()
            )

            return

        if (user_id, VIDEO_ID) in pending_videos:

            await query.edit_message_text(
                "⏳ Your video reward is already processing.\n\n"
                "Please wait 10 seconds.",
                reply_markup=main_menu()
            )

            return

        pending_videos.add(
            (user_id, VIDEO_ID)
        )

        try:

            await query.message.reply_video(
                video=VIDEO_URL,
                caption=(
                    "🎬 Watch this video\n\n"
                    "⏱️ Watch for 10 seconds.\n"
                    "🪙 Reward: +10 Coins"
                ),
                supports_streaming=True
            )

            await query.edit_message_text(
                "🎬 Video sent!\n\n"
                "⏱️ Watch for 10 seconds.\n"
                "🪙 Your +10 Coins reward is processing...",
                reply_markup=main_menu()
            )

            asyncio.create_task(
                reward_after_watch(
                    context.bot,
                    query.message.chat_id,
                    user_id,
                    username
                )
            )

        except Exception as error:

            pending_videos.discard(
                (user_id, VIDEO_ID)
            )

            print("VIDEO ERROR:")
            print(str(error))

            await query.edit_message_text(
                "❌ Sorry, the video could not be loaded.\n\n"
                "Please try again later.",
                reply_markup=main_menu()
            )

    # BALANCE
    elif query.data == "balance":

        coins = get_user(
            user_id,
            username
        )

        await query.edit_message_text(
            "💰 Your Balance\n\n"
            f"🪙 Coins: {coins}\n\n"
            "💵 1000 Coins = ₹10",
            reply_markup=main_menu()
        )

    # WITHDRAW
    elif query.data == "withdraw":

        coins = get_user(
            user_id,
            username
        )

        await query.edit_message_text(
            "💸 Withdraw\n\n"
            f"🪙 Your Balance: {coins} Coins\n\n"
            "Withdrawal options:\n\n"
            "1000 Coins → ₹10\n"
            "2000 Coins → ₹20\n"
            "3000 Coins → ₹30\n"
            "4000 Coins → ₹40\n"
            "5000 Coins → ₹50\n"
            "10000 Coins → ₹100\n\n"
            "🏦 UPI withdrawal will be added next.",
            reply_markup=main_menu()
        )

    # HELP
    elif query.data == "help":

        await query.edit_message_text(
            "ℹ️ Help\n\n"
            "🎬 Watch Video\n"
            "Watch videos and earn coins.\n\n"
            "💰 Balance\n"
            "Check your coin balance.\n\n"
            "💸 Withdraw\n"
            "Withdraw your INR rewards.\n\n"
            "🪙 1000 Coins = ₹10",
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
