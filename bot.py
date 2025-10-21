# bot.py
import os
import subprocess
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import uuid
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
ACR_HOST = os.getenv("ACR_HOST")
ACR_ACCESS_KEY = os.getenv("ACR_ACCESS_KEY")
ACR_ACCESS_SECRET = os.getenv("ACR_ACCESS_SECRET")

DOWNLOAD_DIR = "/tmp"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎧 Salom! Menga video, audio yoki link yuboring — men qo‘shiqni topaman va yuklab beraman.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Iltimos, kuting...")

    file_path = None
    url = update.message.text.strip() if update.message.text else None
    uid = str(uuid.uuid4())
    base_path = os.path.join(DOWNLOAD_DIR, uid)

    # 1. Agar foydalanuvchi URL yuborgan bo‘lsa
    if url and (url.startswith("http://") or url.startswith("https://")):
        out_template = base_path + ".%(ext)s"
        cmd = ["yt-dlp", "-f", "best", "-o", out_template, url]
        try:
            subprocess.run(cmd, check=True, text=True, capture_output=True, timeout=180)
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(uid):
                    file_path = os.path.join(DOWNLOAD_DIR, f)
                    break
        except subprocess.CalledProcessError:
            await msg.edit_text("⚠️ Video yuklab bo‘lmadi.")
            return

    # 2. Agar foydalanuvchi video, audio yoki voice yuborsa
    elif update.message.video or update.message.audio or update.message.voice or update.message.video_note:
        tg_file = (
            update.message.video or
            update.message.audio or
            update.message.voice or
            update.message.video_note
        )
        new_file = await tg_file.get_file()
        file_path = base_path + ".mp4"
        await new_file.download_to_drive(file_path)

    else:
        await msg.edit_text("⚠️ Faqat link, video yoki audio yuboring.")
        return

    # 3. Audio ajratamiz
    audio_path = base_path + ".mp3"
    subprocess.run(["ffmpeg", "-y", "-i", file_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", audio_path])

    # 4. Shazam (ACRCloud) orqali aniqlash
    result = identify_music(audio_path)

    # 5. Natijani yuboramiz
    if result:
        title = result.get("title", "Noma’lum")
        artist = result.get("artists", [{}])[0].get("name", "")
        msg_text = f"🎵 Topildi!\n\n**Nom:** {title}\n**Ijrochi:** {artist}"
        await update.message.reply_text(msg_text, parse_mode="Markdown")

        # Audio faylni foydalanuvchiga yuborish
        await update.message.reply_audio(open(audio_path, "rb"))
    else:
        await update.message.reply_text("😔 Qo‘shiqni aniqlab bo‘lmadi.")

    try:
        os.remove(file_path)
        os.remove(audio_path)
    except:
        pass

def identify_music(audio_file):
    import hmac, hashlib, base64, time

    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))

    string_to_sign = (
        http_method + "\n" + http_uri + "\n" + ACR_ACCESS_KEY + "\n" + data_type + "\n" + signature_version + "\n" + timestamp
    )

    sign = base64.b64encode(
        hmac.new(ACR_ACCESS_SECRET.encode('ascii'), string_to_sign.encode('ascii'), digestmod=hashlib.sha1).digest()
    ).decode('ascii')

    files = {'sample': open(audio_file, 'rb')}
    data = {
        'access_key': ACR_ACCESS_KEY,
        'data_type': data_type,
        'signature_version': signature_version,
        'signature': sign,
        'sample_bytes': os.path.getsize(audio_file),
        'timestamp': timestamp,
    }

    try:
        r = requests.post(ACR_HOST + "/v1/identify", files=files, data=data, timeout=15)
        return r.json().get('metadata', {}).get('music', [{}])[0]
    except Exception as e:
        print("ACR Error:", e)
        return None

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.run_polling()
