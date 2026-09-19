# 🤖 Reward Bot - Telegram Bot for Render

A simple, robust Python Telegram Bot built with `python-telegram-bot` and `Flask`, configured for deployment as a **Web Service** on **Render.com**.

---

## 📋 Features

- **Long Polling Only**: Direct message fetching from Telegram servers (No webhooks).
- **Background Flask Server**: Satisfies Render's port binding and health check requirements.
- **Secure Configuration**: Reads `BOT_TOKEN` strictly from environment variables.
- **Zero Database Required**: Stateless, fast, and simple.

---

## 📱 Beginner Step-by-Step Guide (Using an Android Phone)

You can set up and deploy this entire bot directly from your Android smartphone without needing a computer!

### Step 1: Get Your Bot Token from Telegram (@BotFather)

1. Open the **Telegram app** on your Android phone.
2. Tap the search icon (top right) and search for `@BotFather` (look for the blue verified checkmark).
3. Tap **Start** (or send `/start`).
4. Send the command:
   ```text
   /newbot
   ```
5. Choose a display name for your bot (e.g., `My Reward Bot`).
6. Choose a username ending in `bot` (e.g., `reward_test_2026_bot`).
7. BotFather will reply with your **API Token** (e.g., `7123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).
8. Long-press the token and copy it to your clipboard. **Keep this secret!**

---

### Step 2: Create a GitHub Repository on Android

1. Open **Google Chrome** on your Android phone.
2. Go to [github.com](https://github.com) and log in (or sign up for free).
3. Tap the **+** icon at the top and select **New repository**.
4. Repository name: `reward-bot`.
5. Select **Public** or **Private**, then tap **Create repository**.
6. On the new repository page, tap **creating a new file**:
   - **File 1**:
     - Name: `bot.py`
     - Content: Paste the exact content of `bot.py`.
     - Tap **Commit changes**.
   - **File 2**:
     - Tap **Add file** > **Create new file**.
     - Name: `requirements.txt`
     - Content:
       ```text
       python-telegram-bot==21.11.1
       Flask==3.1.0
       ```
     - Tap **Commit changes**.
   - **File 3**:
     - Tap **Add file** > **Create new file**.
     - Name: `README.md`
     - Content: Paste this README file.
     - Tap **Commit changes**.

---

### Step 3: Deploy to Render.com on Android

1. Open Chrome on your Android phone and go to [render.com](https://render.com).
2. Tap **Sign Up** or **Sign In** (you can sign in with your GitHub account).
3. On your Render Dashboard, tap the **New +** button at the top right.
4. Select **Web Service**.
5. Choose **Build and deploy from a Git repository**.
6. Connect your GitHub account and choose your `reward-bot` repository.
7. Fill in the following **Render Settings**:

| Setting | Value |
| :--- | :--- |
| **Name** | `reward-bot` (or any name you like) |
| **Region** | Choose the one closest to you (e.g., Oregon, Frankfurt, Singapore) |
| **Branch** | `main` |
| **Root Directory** | *(Leave blank)* |
| **Runtime** | `Python` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python bot.py` |
| **Instance Type** | `Free` |

8. Scroll down to **Environment Variables**:
   - Tap **Add Environment Variable**.
   - **Key**: `BOT_TOKEN`
   - **Value**: Paste your token from BotFather (e.g., `7123456789:ABCdef...`).
9. Tap **Deploy Web Service** (at the bottom of the page).

---

### Step 4: Verify Deployment

1. Watch the **Logs** tab on Render.
2. Within 1-2 minutes, you will see:
   ```text
   Flask server started in background thread.
   Reward Bot started with long polling (Webhooks are disabled).
   ```
3. Copy your Render service URL (e.g., `https://reward-bot-xxxx.onrender.com`).
4. Open the URL in your Android phone browser:
   - You should see the exact message:
     ```text
     Telegram Bot is running!
     ```

---

### Step 5: Test the Bot on Telegram

1. Open Telegram on your phone and search for your bot username.
2. Tap **Start** or send `/start`:
   - Bot replies:
     ```text
     👋 Welcome to Reward Bot! 🤖
     Your Telegram bot is working successfully! ✅
     ```
3. Send `/help`:
   - Bot replies:
     ```text
     /start - Start the bot
     /help - Show help
     /about - About the bot
     ```
4. Send `/about`:
   - Bot replies:
     ```text
     Reward Bot is a simple, lightweight Telegram bot designed to distribute rewards, notifications, and manage interactive community tasks on Telegram.
     ```

---

## ⚙️ Environment Variables Reference

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `BOT_TOKEN` | **Yes** | *None* | Your Telegram Bot token obtained from @BotFather |
| `PORT` | No | `10000` | Port for Flask web server (Render automatically sets this) |