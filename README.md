# 🤖 Telegram Bot Simple

Простой телеграм-бот с базовыми командами, созданный для изучения основ разработки ботов на Python.

## ✨ Возможности

- `/start` - Приветствие и запуск бота
- `/help` - Список доступных команд
- `/about` - Информация о боте и авторе
- `/ping` - Проверка работоспособности бота

## 🛠 Технологии

- Python 3.12+
- python-telegram-bot
- python-dotenv

## 📦 Установка и запуск

### 1. Создание проекта
```bash 
mkdir tg-bot-simple
cd tg-bot-simple
```
### 2. Виртуальное окружение
```bash
python -m venv .venv
.venv\Scripts\activate.bat
```
### 3. Установка зависимостей
```bash
pip install python-telegram-bot python-dotenv
```
### 4. Создание файлов
### 5. Получение токена и создание .env
#### .env 
```pycon
TOKEN=ваш_токен_бота
```
### 6. Запуск 
```bash
python main.py
```