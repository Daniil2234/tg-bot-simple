# main.py
import logging
import os
from datetime import datetime
from typing import List
from dotenv import load_dotenv
import telebot
from telebot import types
import requests
from db import init_db, add_note, list_notes, update_note, delete_note, find_notes, get_note_count, list_all_notes, \
    get_combined_stats

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s-%(levelname)s-%(message)s'
)

load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("В .env нет TOKEN")
bot = telebot.TeleBot(TOKEN)


# ================ ВАШИ ОРИГИНАЛЬНЫЕ ФУНКЦИИ ================
def fetch_weather_moscow_open_meteo() -> str:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 55.7558,
        "longitude": 37.6173,
        "current": "temperature_2m",
        "timezone": "Europe/Moscow"
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        t = r.json()["current"]["temperature_2m"]
        return f"Москва: сейчас {round(t)}°C"
    except Exception:
        return "Не удалось получить погоду."


def parse_ints_from_text(text: str) -> List[int]:
    text = text.replace(",", " ")
    tokens = [tok for tok in text.split() if not tok.startswith("/")]
    nums = []
    for tok in tokens:
        try:
            nums.append(int(tok))
        except ValueError:
            continue
    return nums


# ================ КЛАВИАТУРА ================
def make_main_kb() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('/about', '/sum', '/max')
    kb.row('/help', '/confirm', '/weather')
    kb.row('/ping', '/hide', '/show')
    # Команды для заметок
    kb.row('/note_add', '/note_list', '/note_find')
    kb.row('/note_edit', '/note_del', '/note_count')
    kb.row('/note_export', '/stats')
    return kb


# ================ ОСНОВНЫЕ КОМАНДЫ ================
@bot.message_handler(commands=['start'])
def start(message):
    init_db()  # Инициализируем БД при старте
    keyboard = make_main_kb()
    bot.send_message(
        message.chat.id,
        "Привет! Я бот с системой заметок и полезными командами! Напиши /help",
        reply_markup=keyboard
    )


@bot.message_handler(commands=['help'])
def help_cmd(message):
    keyboard = make_main_kb()
    help_text = """
📋 **Основные команды:**
/start - начать работу
/help - эта справка
/about - о боте
/ping - проверка работы бота

🧮 **Математика:**
/sum - сложить числа
/max - найти максимум

🌤️ **Погода:**
/weather - погода в Москве

🔄 **Управление:**
/confirm - подтверждение действия
/hide - скрыть клавиатуру
/show - показать клавиатуру

📝 **Система заметок:**
/note_add - добавить заметку
/note_list - список заметок
/note_find - поиск заметок
/note_edit - редактировать заметку
/note_del - удалить заметку
/note_count - количество заметок
/note_export - экспорт в файл
/stats - статистика
"""
    bot.send_message(message.chat.id, help_text, reply_markup=keyboard)


@bot.message_handler(commands=['weather'])
def weather_command(message):
    weather_info = fetch_weather_moscow_open_meteo()
    bot.send_message(message.chat.id, weather_info, reply_markup=make_main_kb())


@bot.message_handler(commands=['about'])
def about_cmd(message):
    keyboard = make_main_kb()
    bot.send_message(
        message.chat.id,
        "Это бот с системой заметок и полезными командами, созданный с целью приобретения первых практических навыков в создании телеграмм ботов!\nАвтор бота: Седохин Даниил Алексеевич",
        reply_markup=keyboard
    )


@bot.message_handler(commands=['ping'])
def ping_cmd(message):
    bot.reply_to(message, "Pong! Бот работает исправно! ✅")


@bot.message_handler(commands=['hide'])
def hide_kb(message):
    remove_kb = types.ReplyKeyboardRemove()
    bot.send_message(
        message.chat.id,
        "Клавиатура скрыта. Используйте /show чтобы вернуть её.",
        reply_markup=remove_kb
    )


@bot.message_handler(commands=['show'])
def show_kb(message):
    keyboard = make_main_kb()
    bot.send_message(
        message.chat.id,
        "Клавиатура возвращена!",
        reply_markup=keyboard
    )


# ================ МАТЕМАТИЧЕСКИЕ КОМАНДЫ ================
@bot.message_handler(commands=["sum"])
def cmd_sum(m: types.Message) -> None:
    logging.info(f'/sum от {m.from_user.first_name}{m.from_user.id}:{m.text}')
    nums = parse_ints_from_text(m.text)
    logging.info(f'распознаны числа: {nums}')

    if not nums:
        bot.send_message(m.chat.id, "Введите числа через пробел или запятую:")
        bot.register_next_step_handler(m, on_sum_numbers)
    else:
        bot.reply_to(m, f"Сумма: {sum(nums)}")


def on_sum_numbers(m: types.Message) -> None:
    nums = parse_ints_from_text(m.text)
    logging.info("KB-sum next step from id=%s text=%r -> %r", m.from_user.id if m.from_user else "?", m.text, nums)

    if not nums:
        bot.reply_to(m, "Не вижу чисел. Пример: 2 3 10")
        bot.send_message(m.chat.id, "Попробуйте еще раз. Введите числа:")
        bot.register_next_step_handler(m, on_sum_numbers)
    else:
        bot.reply_to(m, f"Сумма: {sum(nums)}")
        bot.send_message(m.chat.id, "Что еще хотите сделать?", reply_markup=make_main_kb())


@bot.message_handler(commands=["max"])
def cmd_max(m: types.Message) -> None:
    logging.info(f'/max от {m.from_user.first_name}{m.from_user.id}:{m.text}')
    nums = parse_ints_from_text(m.text)
    logging.info(f'распознаны числа: {nums}')

    if not nums:
        bot.send_message(m.chat.id, "Введите числа через пробел или запятую для поиска максимума:")
        bot.register_next_step_handler(m, on_max_numbers)
    else:
        bot.reply_to(m, f"Максимум: {max(nums)}")


def on_max_numbers(m: types.Message) -> None:
    nums = parse_ints_from_text(m.text)
    logging.info("KB-max next step from id=%s text=%r -> %r", m.from_user.id if m.from_user else "?", m.text, nums)

    if not nums:
        bot.reply_to(m, "Не вижу чисел. Пример: 2 3 10")
        bot.send_message(m.chat.id, "Попробуйте еще раз. Введите числа:")
        bot.register_next_step_handler(m, on_max_numbers)
    else:
        bot.reply_to(m, f"Максимум: {max(nums)}")
        bot.send_message(m.chat.id, "Что еще хотите сделать?", reply_markup=make_main_kb())


# ================ КОМАНДА ПОДТВЕРЖДЕНИЯ ================
@bot.message_handler(commands=['confirm'])
def confirm_cmd(m):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton('✅ Да', callback_data='confirm:yes'),
        types.InlineKeyboardButton('❌ Нет', callback_data='confirm:no'),
        types.InlineKeyboardButton('🤔 Возможно', callback_data='confirm:maybe'),
    )
    kb.add(
        types.InlineKeyboardButton('🔄 Повторить позже', callback_data='confirm:later'),
        types.InlineKeyboardButton('🚫 Отмена', callback_data='confirm:cancel'),
    )
    bot.send_message(m.chat.id, 'Подтверждение? Выберите вариант:', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('confirm'))
def on_confirm(c):
    choice = c.data.split(':', 1)[1]
    responses = {
        'yes': '✅ Действие подтверждено!',
        'no': '❌ Действие отклонено!',
        'maybe': '🤔 Выбрано "Возможно". Решите позже.',
        'later': '🔄 Отложено. Напомнить через час.',
        'cancel': '🚫 Действие отменено.'
    }

    bot.answer_callback_query(c.id, 'Принято')
    bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    bot.send_message(c.message.chat.id, responses.get(choice, 'Неизвестный выбор'))


# ================ СИСТЕМА ЗАМЕТОК ================
@bot.message_handler(commands=['note_add'])
def note_add_start(message):
    bot.reply_to(message, "📝 Введите текст для новой заметки:")
    bot.register_next_step_handler(message, on_note_add_text)


def on_note_add_text(message):
    text = message.text.strip()
    if not text:
        bot.reply_to(message, "❌ Текст не может быть пустым. Попробуйте еще раз: /note_add")
        return

    user_id = message.from_user.id
    note_id = add_note(user_id, text)

    if note_id > 0:
        bot.reply_to(message, f"✅ Заметка #{note_id} добавлена!")
    else:
        bot.reply_to(message, f"❌ Достигнут лимит заметок (50 шт.). Удалите старые, чтобы добавить новые.")


@bot.message_handler(commands=['note_list'])
def note_list(message):
    user_id = message.from_user.id
    user_notes = list_notes(user_id)

    if not user_notes:
        bot.reply_to(message, "📭 У вас пока нет заметок. Используйте /note_add чтобы добавить первую.")
        return

    response = "📋 Ваши последние заметки:\n"
    for note in user_notes:
        created = note['created_at'].split()[0] if note['created_at'] else "дата неизвестна"
        response += f"\n#{note['id']} ({created}):\n{note['text'][:100]}"
        if len(note['text']) > 100:
            response += "..."
        response += "\n" + "-" * 30

    bot.reply_to(message, response)


@bot.message_handler(commands=['note_find'])
def note_find_start(message):
    bot.reply_to(message, "🔍 Введите текст для поиска в заметках:")
    bot.register_next_step_handler(message, on_note_find_query)


def on_note_find_query(message):
    query_text = message.text.strip()
    if not query_text:
        bot.reply_to(message, "❌ Поисковый запрос не может быть пустым. Попробуйте еще раз: /note_find")
        return

    user_id = message.from_user.id
    found_notes = find_notes(user_id, query_text)

    if not found_notes:
        bot.reply_to(message, f"🔍 Ничего не найдено по запросу «{query_text}».")
        return

    response = f"🔍 Результаты поиска («{query_text}»):\n"
    for note in found_notes:
        response += f"\n#{note['id']}: {note['text'][:150]}"
        if len(note['text']) > 150:
            response += "..."

    bot.reply_to(message, response)


@bot.message_handler(commands=['note_count'])
def note_count(message):
    user_id = message.from_user.id
    count = get_note_count(user_id)

    BAR_CHAR_FILLED = '█'
    BAR_CHAR_EMPTY = '░'
    BAR_LENGTH = 20

    filled_count = int((count / 50) * BAR_LENGTH)
    empty_count = BAR_LENGTH - filled_count
    histogram = f"{BAR_CHAR_FILLED * filled_count}{BAR_CHAR_EMPTY * empty_count}"

    response = (
        f"📊 Количество заметок: {count} из 50\n"
        f"Прогресс: `{histogram}`\n"
        f"Использовано {count}/50 слотов ({count * 2}%)\n"
    )

    if count >= 50:
        response += "\n⚠️ Лимит достигнут! Удалите старые заметки, чтобы добавить новые."

    bot.reply_to(message, response, parse_mode='Markdown')


@bot.message_handler(commands=['note_del'])
def note_del_start(message):
    bot.reply_to(message, "🗑️ Введите ID заметки, которую хотите удалить:")
    bot.register_next_step_handler(message, on_note_del_id)


def on_note_del_id(message):
    try:
        note_id = int(message.text.strip())
    except ValueError:
        bot.reply_to(message, "❌ ID должен быть числом. Попробуйте еще раз: /note_del")
        return

    user_id = message.from_user.id
    success = delete_note(user_id, note_id)

    if success:
        bot.reply_to(message, f"✅ Заметка #{note_id} удалена.")
    else:
        bot.reply_to(message, f"❌ Заметка #{note_id} не найдена или у вас нет прав для её удаления.")


@bot.message_handler(commands=['note_edit'])
def note_edit_start(message):
    bot.reply_to(message, "✏️ Введите ID заметки для редактирования:")
    bot.register_next_step_handler(message, on_note_edit_id)


def on_note_edit_id(message):
    try:
        note_id = int(message.text.strip())
    except ValueError:
        bot.reply_to(message, "❌ ID должен быть числом. Попробуйте еще раз: /note_edit")
        return

    user_id = message.from_user.id
    user_notes = list_all_notes(user_id)

    if not any(note['id'] == note_id for note in user_notes):
        bot.reply_to(message, f"❌ Заметка #{note_id} не найдена. Попробуйте еще раз: /note_edit")
        return

    bot.reply_to(message, f"✏️ Теперь введите новый текст для заметки #{note_id}:")
    bot.register_next_step_handler(message, on_note_edit_text, note_id=note_id)


def on_note_edit_text(message, note_id: int):
    new_text = message.text.strip()
    if not new_text:
        bot.reply_to(message, "❌ Текст не может быть пустым. Редактирование отменено.")
        return

    user_id = message.from_user.id
    success = update_note(user_id, note_id, new_text)

    if success:
        bot.reply_to(message, f"✅ Заметка #{note_id} успешно изменена.")
    else:
        bot.reply_to(message, f"❌ Произошла ошибка при изменении заметки #{note_id}.")


@bot.message_handler(commands=['note_export'])
def note_export(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"

    all_notes = list_all_notes(user_id)
    if not all_notes:
        bot.reply_to(message, "❌ У вас нет заметок для экспорта.")
        return

    today_str = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Формируем текстовый файл
    content = f"Экспорт заметок для пользователя @{username}\n"
    content += f"Дата экспорта: {today_str}\n"
    content += f"Всего заметок: {len(all_notes)}\n"
    content += "=" * 50 + "\n\n"

    for note in all_notes:
        content += f"Заметка #{note['id']}\n"
        content += f"Дата создания: {note['created_at']}\n"
        content += "-" * 30 + "\n"
        content += note['text'] + "\n"
        content += "=" * 50 + "\n\n"

    file_path = f"notes_export_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        with open(file_path, 'rb') as f:
            bot.send_document(
                message.chat.id,
                f,
                caption=f"✅ Экспорт завершен!\nФайл содержит {len(all_notes)} заметок."
            )

    except Exception as e:
        logging.error(f"Ошибка при экспорте заметок для user_id {user_id}: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при создании файла экспорта.")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = message.from_user.id
    stats = get_combined_stats(user_id)

    total_notes = stats['total_notes']

    BAR_CHAR_FILLED = '█'
    BAR_CHAR_EMPTY = '░'
    BAR_LENGTH = 20

    filled_count = int((total_notes / 50) * BAR_LENGTH)
    empty_count = BAR_LENGTH - filled_count
    histogram = f"{BAR_CHAR_FILLED * filled_count}{BAR_CHAR_EMPTY * empty_count}"

    response_text = (
        f"📊 **Статистика заметок**\n\n"
        f"**Использование слотов:**\n"
        f"`{histogram}`\n"
        f"Заметок: **{total_notes}** из **50** ({total_notes * 2}%)\n"
        f"📝 **Суммарный объем:** `{stats['total_chars']:,}` символов\n"
        f"────────────────────\n"
        f"**История действий (всего):**\n"
        f"✅ Создано: **{stats['total_created']}**\n"
        f"✍️ Изменено: **{stats['total_edited']}**\n"
        f"🗑️ Удалено: **{stats['total_deleted']}**\n"
        f"────────────────────\n"
        f"**Активность за неделю:**\n"
        f"✅ Создано: **{stats['weekly_created']}**\n"
        f"✍️ Изменено: **{stats['weekly_edited']}**\n"
        f"🗑️ Удалено: **{stats['weekly_deleted']}**\n"
        f"────────────────────\n"
        f"ℹ️ Используйте /note_count для быстрого просмотра количества заметок"
    )

    bot.reply_to(message, response_text, parse_mode='Markdown')


# ================ ОБРАБОТЧИКИ КНОПОК ================
@bot.message_handler(func=lambda m: m.text and m.text.strip() == "/sum")
def kb_sum(m: types.Message) -> None:
    bot.send_message(m.chat.id, "Введите числа через пробел или запятую:")
    bot.register_next_step_handler(m, on_sum_numbers)


@bot.message_handler(func=lambda m: m.text and m.text.strip() == "/max")
def kb_max(m: types.Message) -> None:
    bot.send_message(m.chat.id, "Введите числа через пробел или запятую для поиска максимума:")
    bot.register_next_step_handler(m, on_max_numbers)


# ================ ЗАПУСК БОТА ================
if __name__ == "__main__":
    print("Бот запускается с системой заметок...")
    init_db()  # Инициализация базы данных
    bot.infinity_polling(skip_pending=True)