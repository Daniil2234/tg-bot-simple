import logging
import os
from typing import List
from dotenv import load_dotenv
import telebot
from telebot import types
import requests

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


def fetch_weather_moscow_open_meteo() -> str:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        # координаты мск ("latitude": 55.7558,
        #                "longitude": 37.6173,)
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


@bot.message_handler(commands=['weather'])
def weather_command(message):
    weather_info = fetch_weather_moscow_open_meteo()
    bot.send_message(message.chat.id, weather_info, reply_markup=make_main_kb())


@bot.message_handler(commands=['start'])
def start(message):
    keyboard = make_main_kb()
    bot.send_message(
        message.chat.id,
        "Привет! Я простой бот! Напиши /help",
        reply_markup=keyboard
    )


@bot.message_handler(commands=['help'])
def help_cmd(message):
    keyboard = make_main_kb()
    bot.send_message(
        message.chat.id,
        "/start - начать\n/help - помощь\n/about - о боте\n/ping - проверка работоспособности бота\n/sum - сложить числа\n/max - найти максимум\n/weather - погода в Москве\n/hide - скрыть клавиатуру\n/show - показать клавиатуру\n/confirm - подтверждение действия",
        reply_markup=keyboard
    )


@bot.message_handler(commands=['about'])
def about_cmd(message):
    keyboard = make_main_kb()
    bot.send_message(
        message.chat.id,
        "Это простой бот с примитивными командами, созданный с целью приобретения первых практических навыков в создании телеграмм ботов!\nАвтор бота: Седохин Даниил Алексеевич",
        reply_markup=keyboard
    )


@bot.message_handler(commands=['ping'])
def ping_cmd(message):
    bot.reply_to(message, "Pong! Бот работает исправно! ✅")


@bot.message_handler(commands=['hide'])
def hide_kb(message):
    # Создаем пустую клавиатуру для скрытия
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


def is_int_token(token: str) -> bool:
    """Проверяет, является ли токен целым числом"""
    try:
        int(token)
        return True
    except ValueError:
        return False


def parse_ints_from_text(text: str) -> List[int]:
    """Выделяет из текста целые числа: нормализует запятые, игнорирует токены-команды."""
    text = text.replace(",", " ")
    tokens = [tok for tok in text.split() if not tok.startswith("/")]

    nums = []
    for tok in tokens:
        try:
            nums.append(int(tok))
        except ValueError:
            continue
    return nums


@bot.message_handler(commands=["sum"])
def cmd_sum(m: types.Message) -> None:
    # Логируем входящую команду
    logging.info(f'/sum от {m.from_user.first_name}{m.from_user.id}:{m.text}')
    nums = parse_ints_from_text(m.text)

    # Логируем результат парсинга
    logging.info(f'распознаны числа: {nums}')

    # Для команды /sum обрабатываем числа из текста команды
    if not nums:
        # Если чисел нет, просим ввести их отдельно
        bot.send_message(m.chat.id, "Введите числа через пробел или запятую:")
        bot.register_next_step_handler(m, on_sum_numbers)
    else:
        bot.reply_to(m, f"Сумма: {sum(nums)}")


@bot.message_handler(func=lambda m: m.text and m.text.strip() == "/sum")
def kb_sum(m: types.Message) -> None:
    # Обработчик для кнопки /sum
    bot.send_message(m.chat.id, "Введите числа через пробел или запятую:")
    bot.register_next_step_handler(m, on_sum_numbers)


def on_sum_numbers(m: types.Message) -> None:
    # Обработчик введенных чисел
    nums = parse_ints_from_text(m.text)
    logging.info("KB-sum next step from id=%s text=%r -> %r", m.from_user.id if m.from_user else "?", m.text, nums)

    if not nums:
        bot.reply_to(m, "Не вижу чисел. Пример: 2 3 10")
        # Предлагаем попробовать еще раз
        bot.send_message(m.chat.id, "Попробуйте еще раз. Введите числа:")
        bot.register_next_step_handler(m, on_sum_numbers)
    else:
        bot.reply_to(m, f"Сумма: {sum(nums)}")
        # Возвращаем основную клавиатуру
        bot.send_message(m.chat.id, "Что еще хотите сделать?", reply_markup=make_main_kb())


# Команда /max - нахождение максимума
@bot.message_handler(commands=["max"])
def cmd_max(m: types.Message) -> None:
    # Логируем входящую команду
    logging.info(f'/max от {m.from_user.first_name}{m.from_user.id}:{m.text}')
    nums = parse_ints_from_text(m.text)

    # Логируем результат парсинга
    logging.info(f'распознаны числа: {nums}')

    if not nums:
        # Если чисел нет, просим ввести их отдельно
        bot.send_message(m.chat.id, "Введите числа через пробел или запятую для поиска максимума:")
        bot.register_next_step_handler(m, on_max_numbers)
    else:
        bot.reply_to(m, f"Максимум: {max(nums)}")


@bot.message_handler(func=lambda m: m.text and m.text.strip() == "/max")
def kb_max(m: types.Message) -> None:
    # Обработчик для кнопки /max
    bot.send_message(m.chat.id, "Введите числа через пробел или запятую для поиска максимума:")
    bot.register_next_step_handler(m, on_max_numbers)


def on_max_numbers(m: types.Message) -> None:
    # Обработчик введенных чисел для максимума
    nums = parse_ints_from_text(m.text)
    logging.info("KB-max next step from id=%s text=%r -> %r", m.from_user.id if m.from_user else "?", m.text, nums)

    if not nums:
        bot.reply_to(m, "Не вижу чисел. Пример: 2 3 10")
        # Предлагаем попробовать еще раз
        bot.send_message(m.chat.id, "Попробуйте еще раз. Введите числа:")
        bot.register_next_step_handler(m, on_max_numbers)
    else:
        bot.reply_to(m, f"Максимум: {max(nums)}")
        # Возвращаем основную клавиатуру
        bot.send_message(m.chat.id, "Что еще хотите сделать?", reply_markup=make_main_kb())


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
    bot.send_message(m.chat.id, 'Подтвердить действие? Выберите вариант:', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('confirm'))
def on_confirm(c):
    # Извлекаем выбор пользователя
    choice = c.data.split(':', 1)[1]  # yes, no, maybe, later, cancel

    # Словарь с ответами для разных вариантов
    responses = {
        'yes': '✅ Действие подтверждено!',
        'no': '❌ Действие отклонено!',
        'maybe': '🤔 Выбрано "Возможно". Решите позже.',
        'later': '🔄 Отложено. Напомнить через час.',
        'cancel': '🚫 Действие отменено.'
    }

    bot.answer_callback_query(c.id, 'Принято')

    # Убираем кнопки после выбора
    bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)

    # Отправляем соответствующий ответ
    bot.send_message(c.message.chat.id, responses.get(choice, 'Неизвестный выбор'))


def make_main_kb() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('/about', '/sum', '/max')
    kb.row('/help', '/confirm', '/weather')
    kb.row('/ping', '/hide', '/show')
    return kb


if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True)