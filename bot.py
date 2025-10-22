# ===========================================
# UNIVERSAL DOWNLOADER + SHAZAM (AudD API)
# ===========================================

import os
import requests
import yt_dlp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
import tempfile

# .env fayldan tokenlarni yuklaymiz
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
AUDD_API_TOKEN = os.getenv("AUDD_API_TOKEN")

# ===========================================
# 1. /start komandasi
# ===========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Men universal yuklovchi + Shazam botman.\n"
        "Menga link, audio yoki video yuboring — men yuklab, qo‘shiqni aniqlab beraman 🎶"
    )

# ===========================================
# 2. Har xil saytlar uchun yuklab olish funksiyasi
# ===========================================
async def download_media(url: str):
    ydl_opts = {
        "outtmpl": "%(title)s.%(ext)s",
        "format": "best",
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        ydl.download([url])
        filename = ydl.prepare_filename(info)
        return filename, info.get("title", "video")

# ===========================================
# 3. AudD API orqali Shazam funksiyasi
# ===========================================
def recognize_music(file_path: str):
    url = "https://api.audd.io/"
    data = {
        "api_token": AUDD_API_TOKEN,
        "return": "timecode,apple_music,spotify",
    }

    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, data=data, files=files)
        result = response.json()

    if result.get("status") == "success" and result.get("result"):
        song = result["result"]
        title = song.get("title", "Noma'lum qo‘shiq")
        artist = song.get("artist", "Noma'lum ijrochi")
        album = song.get("album", "")
        release_date = song.get("release_date", "")
        spotify = song.get("spotify", {}).get("external_urls", {}).get("spotify", "")

        msg = f"🎵 {title}\n👤 {artist}"
        if album:
            msg += f"\n💿 {album}"
        if release_date:
            msg += f"\n📅 {release_date}"
        if spotify:
            msg += f"\n🔗 [Spotify'da tinglash]({spotify})"

        return msg
    else:
        return "⚠️ Qo‘shiq aniqlanmadi."

# ===========================================
# 4. Foydalanuvchi yuborgan narsani aniqlovchi handler
# ===========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    # Agar link yuborsa — video yuklab olish
    if msg.text and ("http" in msg.text):
        url = msg.text.strip()
        await msg.reply_text("⏳ Video yuklanmoqda, biroz kuting...")

        try:
            filename, title = await download_media(url)
            await msg.reply_text(f"✅ Yuklandi: {title}")
            await msg.reply_video(video=open(filename, "rb"))

            # Shazam orqali aniqlash
            await msg.reply_text("🎧 Qo‘shiq aniqlanmoqda...")
            song_info = recognize_music(filename)
            await msg.reply_text(song_info, parse_mode="Markdown")
            os.remove(filename)
        except Exception as e:
            await msg.reply_text(f"❌ Xatolik: {e}")

    # Agar audio, video yoki voice yuborsa
    elif msg.audio or msg.voice or msg.video:
        await msg.reply_text("🎧 Qo‘shiq aniqlanmoqda...")

        file = msg.audio or msg.voice or msg.video
        file_id = file.file_id
        file_obj = await context.bot.get_file(file_id)

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            await file_obj.download_to_drive(temp_file.name)
            song_info = recognize_music(temp_file.name)
            await msg.reply_text(song_info, parse_mode="Markdown")
            os.remove(temp_file.name)

    else:
        await msg.reply_text("📩 Menga link, audio yoki video yuboring.")

# ===========================================
# 5. Botni ishga tushirish
# ===========================================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
