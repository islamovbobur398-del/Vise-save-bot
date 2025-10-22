import os
import requests
import tempfile
import subprocess
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

# .env fayldan tokenlarni yuklaymiz
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
AUDD_API_TOKEN = os.getenv("AUDD_API_TOKEN")

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Men universal yuklovchi botman.\n\n"
        "Menga quyidagilardan havola yuboring:\n"
        "📱 Instagram, TikTok, YouTube, Pinterest, Threads va boshqalar.\n\n"
        "🎵 Shazam funksiyasi: menga video, audio yoki ovozli xabar yuboring — men qo‘shiq nomini topaman!"
    )

# Shazam funksiyasi (AudD API orqali)
async def recognize_music(file_path):
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"api_token": AUDD_API_TOKEN, "return": "lyrics,timecode"}
        result = requests.post("https://api.audd.io/", data=data, files=files).json()
        return result

# Media fayl (audio/video) yuborilganda
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.effective_attachment.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        await file.download_to_drive(tmp.name)
        result = await recognize_music(tmp.name)

    if result and result.get("result"):
        song = result["result"]
        title = song.get("title", "Noma’lum")
        artist = song.get("artist", "Noma’lum")
        lyrics = song.get("lyrics", "Matn topilmadi.")
        await update.message.reply_text(
            f"🎧 *Qo‘shiq topildi!*\n\n"
            f"🎵 Nomi: {title}\n👤 Ijrochi: {artist}\n\n"
            f"📜 Matn:\n{lyrics[:1000]}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("❌ Afsus, qo‘shiqni aniqlab bo‘lmadi.")

# URL yuborilganda (video yuklash)
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    await update.message.reply_text("⏳ Yuklanmoqda, kuting...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "video.mp4")
            cmd = [
                "yt-dlp",
                "-o", output_path,
                "-f", "mp4",
                url
            ]
            subprocess.run(cmd, check=True)

            await update.message.reply_video(video=open(output_path, "rb"))
            await update.message.reply_text("✅ Yuklab bo‘lindi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")

# Botni ishga tushirish
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.VIDEO, handle_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
