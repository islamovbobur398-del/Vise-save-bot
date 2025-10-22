# ===============================
# 🔹 Universal Downloader Bot — Xatarsiz Dockerfile
# ===============================

FROM python:3.11-slim

# 1. Tizim kutubxonalarini o‘rnatamiz
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    build-essential \
    libffi-dev \
    libnss3 \
    && rm -rf /var/lib/apt/lists/*

# 2. Ishchi papka
WORKDIR /app

# 3. Kutubxonalarni o‘rnatish
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# 4. Fayllarni konteynerga ko‘chirish
COPY . .

# 5. Portni ko‘rsatish (Render avtomatik beradi)
EXPOSE 10000

# 6. Botni ishga tushirish
CMD ["python", "bot.py"]
