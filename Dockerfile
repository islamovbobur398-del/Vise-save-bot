# ===============================
# 🔹 Universal Downloader Bot — Dockerfile
# ===============================

# 1. Python bazasini tanlaymiz
FROM python:3.11-slim

# 2. ffmpeg va boshqa kerakli tizim paketlarini o‘rnatamiz
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

# 3. Ishchi katalogni belgilaymiz
WORKDIR /app

# 4. Talablar faylini nusxalaymiz va o‘rnatamiz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Loyiha fayllarini konteynerga nusxalaymiz
COPY . .

# 6. Ishlaydigan portni belgilaymiz (Render avtomatik PORT beradi)
EXPOSE 10000

# 7. Botni ishga tushirish
CMD ["python", "bot.py"]
