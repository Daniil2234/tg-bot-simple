import os
from dotenv import load_dotenv
import telebot

load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("В .env нет TOKEN")
bot = telebot.TeleBot(TOKEN)

# Команда start для запуска бота
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я простой бот! Напиши /help")

# Команда help для вывода возможностей бота
@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "/start - начать\n/help - помощь\n/about - о боте\n/ping - проверка работоспособности бота")

# Команда about для вывода информации о боте и авторе
@bot.message_handler(commands=['about'])
def about_cmd(message):
    bot.reply_to(message, "Это простой бот с примитивными командами, созданный с целью приобретения первых практических навыков в создании телеграмм ботов!\nАвтор бота: Седохин Даниил Алексеевич")

# Простая проверка бота на работоспособность
@bot.message_handler(commands=['ping'])
def ping_cmd(message):
    bot.reply_to(message, "Pong! Бот работает исправно! ✅")

# Пропуск предыдущих сообщений боту
if __name__ == "__main__":
 bot.infinity_polling(skip_pending=True)

