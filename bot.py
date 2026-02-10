import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = int(os.getenv("OWNER_ID"))      # your telegram ID
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL"))  # -100xxxx

MAX_USERS = 4
ACTIVE_USERS = set()
USER_VIDEOS = {}

app = Client(
    "merge-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

os.makedirs("downloads", exist_ok=True)

# ---------------- START ----------------
@app.on_message(filters.command("start"))
async def start(client, message):
    name = message.from_user.first_name

    text = f"""
✨ **Hi {name}**

🤖 I am a Telegram bot with **video merge feature**
🎬 Supports **MP4 & MKV**

🛠 Maintain by: **@AniWorld_Bots_Hub**
"""

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📢 Channel", url="https://t.me/AniWorld_Bots_Hub"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/H_IN_AT_A")
            ]
        ]
    )

    await message.reply_photo(
        photo="start.jpg",
        caption=text,
        reply_markup=buttons
    )

# ---------------- VIDEO ----------------
@app.on_message(filters.video)
async def add_video(client, message):
    user_id = message.from_user.id

    # user limit check
    if user_id != OWNER_ID:
        ACTIVE_USERS.add(user_id)
        if len(ACTIVE_USERS) > MAX_USERS:
            ACTIVE_USERS.remove(user_id)
            await message.reply("🚫 Bot is busy. Try again later.")
            return

    if user_id not in USER_VIDEOS:
        USER_VIDEOS[user_id] = []

    path = await message.download(
        file_name=f"downloads/{user_id}_{len(USER_VIDEOS[user_id])}.mp4"
    )
    USER_VIDEOS[user_id].append(path)

    await message.reply("✅ 1 video added")

    await client.send_message(
        LOG_CHANNEL,
        f"🎬 Video added\nUser: `{user_id}`\nTotal: {len(USER_VIDEOS[user_id])}"
    )

# ---------------- MERGE ----------------
@app.on_message(filters.command("merge"))
async def merge(client, message):
    user_id = message.from_user.id

    if user_id not in USER_VIDEOS or len(USER_VIDEOS[user_id]) < 2:
        await message.reply("⚠️ Send at least 2 videos.")
        return

    await message.reply("⏳ Merging videos...")

    list_file = f"downloads/{user_id}_list.txt"
    output = f"downloads/{user_id}_merged.mkv"

    with open(list_file, "w") as f:
        for v in USER_VIDEOS[user_id]:
            f.write(f"file '{v}'\n")

    subprocess.run([
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c", "copy", output
    ], check=True)

    await message.reply_video(output)

    for v in USER_VIDEOS[user_id]:
        os.remove(v)
    os.remove(list_file)
    os.remove(output)

    USER_VIDEOS[user_id] = []
    ACTIVE_USERS.discard(user_id)

    await client.send_message(
        LOG_CHANNEL,
        f"✅ Merge done\nUser: `{user_id}`"
    )

app.run()
