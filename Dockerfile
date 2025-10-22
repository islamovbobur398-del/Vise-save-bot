# ===============================
# 🔹 Universal Downloader Bot — Render uchun to‘liq Dockerfile
# ===============================

FROM python:3.11-slim

# 1. Tizim kutubxonalarini o‘rnatish
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    build-essential \
    libffi-dev \
    libnss3 \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. Ishchi katalog
WORKDIR /app

# 3. Pipni yangilash
RUN pip install --upgrade pip setuptools wheel

# 4. Talablar faylini ko‘chirish va o‘rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Barcha fayllarni konteynerga nusxalash
COPY . .

# 6. Render porti (avtomatik)
EXPOSE 10000

# 7. Botni ishga tushirish
CMD ["python", "bot.py"]
