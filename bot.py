import os
import asyncio
import logging
import sqlite3
import threading

from flask import Flask
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

DB_FILE = "reward_bot.db"

VIDEO_URL = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"

VIDEO_ID = "video_1"

REWARD_COINS = 10

WATCH_SECONDS = 10


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# =========================================================
# FLASK SERVER
# =========================================================

flask_app = Flask(__name__)


@flask_app.route("/")
def home():
    return "Reward Bot is running!"


def run_flask():
    port = int(os.environ.get("PORT", 10000))

    flask_app.run(
        host="0.0.0.0",
        port=port
    )


# =========================================================
# DATABASE
# =========================================================

def init_db():

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0
        )
    """)

    # Watched videos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watched_videos (
            user_id INTEGER,
            video_id TEXT,
            PRIMARY KEY (user_id, video_id)
        )
    """)

    conn.commit()

    conn.close()


# =========================================================
# USER FUNCTIONS
# =========================================================

def get_user(user_id):

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT coins FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()

    if result is None:

        cursor.execute(
            "INSERT INTO users (user_id, coins) VALUES (?, ?)",
            (user_id, 0)
        )

        conn.commit()

        coins = 0

    else:

        coins = result[0]

    conn.close()

    return coins


def add_coins(user_id, amount):

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, coins) VALUES (?, ?)",
        (user_id, 0)
    )

    cursor.execute(
        "UPDATE users SET coins = coins + ? WHERE user_id = ?",
        (amount, user_id)
    )

    conn.commit()

    conn.close()


def already_watched(user_id, video_id):

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM watched_videos
        WHERE user_id = ? AND video_id = ?
        """,
        (user_id, video_id)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


def mark_video_watched(user_id, video_id):

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO watched_videos
        (user_id, video_id)
        VALUES (?, ?)
        """,
        (user_id, video_id)
    )

    conn.commit()

    conn.close()


# =========================================================
# MAIN MENU
# =========================================================

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


# =========================================================
# BACK BUTTON
# =========================================================

def back_button():

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="back"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# START COMMAND
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user is None:
        return

    get_user(user.id)

    await update.message.reply_text(

        "🎉 Welcome to Reward Bot!\n\n"
        "Watch videos and earn Coins.\n\n"
        "💰 10 Coins per completed video\n"
        "🇮🇳 1000 Coins = ₹10\n\n"
        "Choose an option below:",

        reply_markup=main_menu()
    )


# =========================================================
# WATCH REWARD FUNCTION
# =========================================================

async def reward_after_watch(
    user_id,
    chat_id,
    bot
):

    try:

        await asyncio.sleep(WATCH_SECONDS)

        # Check again
        if already_watched(user_id, VIDEO_ID):

            return

        # Mark video as watched
        mark_video_watched(user_id, VIDEO_ID)

        # Add coins
        add_coins(user_id, REWARD_COINS)

        # Get updated balance
        coins = get_user(user_id)

        await bot.send_message(

            chat_id=chat_id,

            text=(
                "🎉 Video Completed!\n\n"
                f"🪙 +{REWARD_COINS} Coins added!\n\n"
                f"💰 Your Balance: {coins} Coins\n\n"
                "Keep watching videos to earn more."
            ),

            reply_markup=main_menu()
        )

    except Exception as e:

        logger.error(
            "Reward error: %s",
            e
        )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    user = query.from_user

    user_id = user.id

    # =====================================================
    # WATCH VIDEO
    # =====================================================

    if query.data == "watch_video":

        # Check if already watched
        if already_watched(user_id, VIDEO_ID):

            await query.edit_message_text(

                "🎬 Video Already Watched\n\n"
                "You have already earned Coins from this video.\n\n"
                "New videos will be added later.",

                reply_markup=main_menu()
            )

            return

        # Check pending
        pending_videos = context.application.bot_data.setdefault(
            "pending_videos",
            set()
        )

        if user_id in pending_videos:

            await query.edit_message_text(

                "⏳ Your video is already being processed.\n\n"
                "Please wait 10 seconds.",

                reply_markup=main_menu()
            )

            return

        # Add pending
        pending_videos.add(user_id)

        try:

            # Edit old message
            await query.edit_message_text(
                "🎬 Loading video...\n\n"
                "Watch the video for 10 seconds.\n"
                "After completion you will receive 10 Coins."
            )

            # Send video
            await context.bot.send_video(

                chat_id=query.message.chat_id,

                video=VIDEO_URL,

                caption=(
                    "🎬 Watch this video\n\n"
                    "⏱️ Watch for 10 seconds\n"
                    "🪙 Reward: +10 Coins"
                ),

                supports_streaming=True,

                reply_markup=back_button()
            )

            # Start reward timer
            asyncio.create_task(

                reward_after_watch(
                    user_id,
                    query.message.chat_id,
                    context.bot
                )
            )

        except Exception as e:

            logger.error(
                "Video error: %s",
                e
            )

            await context.bot.send_message(

                chat_id=query.message.chat_id,

                text=(
                    "❌ Video could not be loaded.\n\n"
                    "Please try again."
                ),

                reply_markup=main_menu()
            )

            pending_videos.discard(user_id)


        return


    # =====================================================
    # BALANCE
    # =====================================================

    elif query.data == "balance":

        coins = get_user(user_id)

        await query.edit_message_text(

            "💰 Your Balance\n\n"
            f"🪙 Coins: {coins}\n\n"
            "🇮🇳 Withdrawal Rate:\n"
            "1000 Coins = ₹10",

            reply_markup=main_menu()
        )

        return


    # =====================================================
    # WITHDRAW
    # =====================================================

    elif query.data == "withdraw":

        coins = get_user(user_id)

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
