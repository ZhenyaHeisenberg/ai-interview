# Dockerfile
FROM python:3.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создание директории приложения
WORKDIR /app

# Копирование всех файлов проекта
COPY . .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Открытие порта
EXPOSE 5000

# Переменные окружения
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Запуск приложения
CMD ["python", "app.py"]