# ===========================================
# UNIVERSAL DOWNLOADER + SHAZAM TELEGRAM BOT
# ===========================================

import os
import requests
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
from acrcloud.recognizer import ACRCloudRecognizer
import tempfile
import subprocess

# 🔹 .env fayldan ma'lumotlarni yuklaymiz
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ACR_HOST = os.getenv("ACR_HOST")
ACR_ACCESS_KEY = os.getenv("ACR_ACCESS_KEY")
ACR_ACCESS_SECRET = os.getenv("ACR_ACCESS_SECRET")

# 🔹 Shazam (ACRCloud) sozlamalari
config = {
    "host": ACR_HOST,
    "access_key": ACR_ACCESS_KEY,
    "access_secret": ACR_ACCESS_SECRET,
    "timeout": 10,
}

recognizer = ACRCloudRecognizer(config)

# =====================================================
# 1. Boshlang'ich /start komandasi
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Men universal media yuklovchi botman.\n"
        "Menga istalgan ijtimoiy tarmoq linkini yoki video/audio yuboring 🎥🎵\n"
        "Men uni yuklab beraman va qo‘shiqni aniqlab beraman 🎶"
    )

# =====================================================
# 2. Yuklab olish funksiyasi (har xil saytlar uchun)
# =====================================================
async def download_media(url: str):
    ydl_opts = {
        "outtmpl": "%(title)s.%(ext)s",
        "format": "best",
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        download_url = info.get("url", None)
        title = info.get("title", "video")
        ext = info.get("ext", "mp4")

        filename = f"{title}.{ext}"
        ydl.download([url])
        return filename, title


# =====================================================
# 3. Shazam orqali qo‘shiqni aniqlash funksiyasi
# =====================================================
def recognize_music(file_path: str):
    try:
        result = recognizer.recognize_by_file(file_path, 0)
        if "metadata" in result and "music" in result["metadata"]:
            music_info = result["metadata"]["music"][0]
            title = music_info.get("title", "Noma'lum qo‘shiq")
            artist = music_info.get("artists", [{"name": "Noma'lum ijrochi"}])[0]["name"]
            album = music_info.get("album", {}).get("name", "")
            return f"🎵 {title}\n👤 {artist}\n💿 {album}"
        else:
            return "⚠️ Qo‘shiq aniqlanmadi."
    except Exception as e:
        return f"❌ Xatolik: {e}"


# =====================================================
# 4. Har qanday xabarni avtomatik aniqlovchi handler
# =====================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # 🔹 Agar foydalanuvchi link yuborsa (video yuklash)
    if message.text and ("http" in message.text or "https" in message.text):
        url = message.text.strip()
        await message.reply_text("⏳ Yuklanmoqda, biroz kuting...")

        try:
            filename, title = await download_media(url)
            await message.reply_text(f"✅ Yuklandi: {title}")
            await message.reply_video(video=open(filename, "rb"))
            await message.reply_audio(audio=open(filename, "rb"))

            # 🔹 Shazam orqali aniqlaymiz
            song_info = recognize_music(filename)
            await message.reply_text(song_info)

        except Exception as e:
            await message.reply_text(f"❌ Xatolik yuz berdi: {e}")

    # 🔹 Agar foydalanuvchi audio, video yoki voice yuborsa (Shazam ishlaydi)
    elif message.audio or message.voice or message.video:
        await message.reply_text("🎧 Qo‘shiq aniqlanmoqda...")

        file = message.audio or message.voice or message.video
        file_id = file.file_id
        file_obj = await context.bot.get_file(file_id)

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            await file_obj.download_to_drive(temp_file.name)
            result = recognize_music(temp_file.name)
            await message.reply_text(result)
            os.remove(temp_file.name)

    else:
        await message.reply_text("🔗 Menga ijtimoiy tarmoq linki yoki audio/video yuboring.")


# =====================================================
# 5. Botni ishga tushirish
# =====================================================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
