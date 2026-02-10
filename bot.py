import os
import subprocess
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIG =================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 8207582785  # 🔴 REPLACE with your Telegram ID
MAX_USERS = 4

BASE_DIR = "videos"
os.makedirs(BASE_DIR, exist_ok=True)

active_users = set()
user_videos = {}
# =========================================

app = Client(
    "merge_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------- USER SLOT CHECK ----------
def can_use(user_id):
    if user_id == OWNER_ID:
        return True
    return len(active_users) < MAX_USERS or user_id in active_users

# ---------- START ----------
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "🎬 **Fast Video Merge Bot**\n\n"
        "Send videos → /merge\n"
        "Max 4 users at a time.\n"
        "Owner always allowed."
    )

# ---------- VIDEO HANDLER ----------
@app.on_message(filters.video)
async def handle_video(client, message):
    user_id = message.from_user.id

    if not can_use(user_id):
        await message.reply("🚫 Bot is busy. Try again later.")
        return

    active_users.add(user_id)
    user_videos.setdefault(user_id, [])

    user_dir = f"{BASE_DIR}/{user_id}"
    os.makedirs(user_dir, exist_ok=True)

    video_path = await message.download(file_name=f"{user_dir}/")

    user_videos[user_id].append(video_path)

    await message.reply(
        f"✅ Video added!\n"
        f"Total: **{len(user_videos[user_id])}**"
    )

# ---------- SMART MERGE ----------
@app.on_message(filters.command("merge"))
async def merge(client, message):
    user_id = message.from_user.id
    files = user_videos.get(user_id, [])

    if len(files) < 2:
        await message.reply("⚠ Send at least 2 videos.")
        return

    list_file = f"{BASE_DIR}/{user_id}/list.txt"
    output = f"{BASE_DIR}/{user_id}/merged.mp4"

    with open(list_file, "w") as f:
        for v in files:
            f.write(f"file '{os.path.abspath(v)}'\n")

    status = await message.reply("⏳ Merging (fast mode)...")

    # Try FAST merge
    fast_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output
    ]

    slow_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac",
        output
    ]

    result = subprocess.run(fast_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if result.returncode != 0:
        await status.edit("⚠ Re-encoding for compatibility...")
        subprocess.run(slow_cmd)

    await status.edit("✅ Merge done! Sending video...")
    await message.reply_video(output)

    # Cleanup
    for f in files:
        os.remove(f)

    user_videos[user_id] = []
    active_users.discard(user_id)

# ---------- RUN ----------
print("🚀 Merge bot started")
app.run()
