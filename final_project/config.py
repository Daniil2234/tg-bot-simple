# config.py
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Проверяем, что ключи загружены
if not TELEGRAM_TOKEN:
    print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден в .env файле!")
    exit(1)

# OpenRouter API ключ
if not OPENROUTER_API_KEY:
    print("⚠️  Предупреждение: OPENROUTER_API_KEY не найден в .env файле!")
    print("   Бот будет использовать локальную базу данных")