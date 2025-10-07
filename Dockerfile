# Rasmiy Python image'i asosida konteynerni yaratish
FROM python:3.11-slim

# Loyihani saqlash uchun /app direktoriyasini yaratish va uni ishchi papka (working directory) qilib belgilash
WORKDIR /app

# Loyiha talablarini (requirements) o'rnatish
# Avval requirements faylini nusxalash
COPY requirements.txt .

# Talablarni o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Qolgan barcha fayllarni (main.py, handlers.py, db.py, keyboards.py va h.k.) nusxalash
COPY . .

# Botning asosiy buyrug'ini belgilash (main.py ni ishga tushirish)
# Agar sizda webhook o'rniga polling bo'lsa, 'main.py' ni ishga tushirish yetarli.
CMD ["python", "main.py"]
