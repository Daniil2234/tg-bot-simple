import logging
import os
from typing import List
from dotenv import load_dotenv
import telebot
from telebot import types
import requests
from db import init_db, list_models, get_active_model, set_active_model
from openrouter import chat_once, OpenRouterError
from db import init_db, list_models, get_active_model, set_active_model, get_model_by_id

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


def is_int_token(token: str) -> bool:
    try:
        int(token)
        return True
    except ValueError:
        return False


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


# ================ КОМАНДЫ БОТА ================
def make_main_kb() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('/about', '/sum', '/max')
    kb.row('/help', '/confirm', '/weather')
    kb.row('/ping', '/hide', '/show')
    # команды для OpenRouter
    kb.row('/models', '/model', '/ask')
    kb.row('/ask_model')
    return kb


@bot.message_handler(commands=['start'])
def start(message):
    init_db()  # Инициализируем БД при старте
    keyboard = make_main_kb()
    bot.send_message(
        message.chat.id,
        "Привет! Я простой бот с поддержкой OpenRouter AI! Напиши /help",
        reply_markup=keyboard
    )


@bot.message_handler(commands=['help'])
def help_cmd(message):
    keyboard = make_main_kb()
    bot.send_message(
        message.chat.id,
        "/start - начать\n"
        "/help - помощь\n"
        "/about - о боте\n"
        "/ping - проверка работоспособности бота\n"
        "/sum - сложить числа\n"
        "/max - найти максимум\n"
        "/weather - погода в Москве\n"
        "/hide - скрыть клавиатуру\n"
        "/show - показать клавиатуру\n"
        "/confirm - подтверждение действия\n\n"
        "=== OpenRouter AI ===\n"
        "/models - список моделей AI\n"
        "/model <id> - выбрать активную модель\n"
        "/ask <вопрос> - задать вопрос активной модели\n"
        "/ask_model <id> <вопрос> - задать вопрос конкретной модели (без смены активной)\n"
        "Пример: /ask_model 3 Какая сегодня погода?",
        reply_markup=keyboard
    )


@bot.message_handler(commands=['weather'])
def weather_command(message):
    weather_info = fetch_weather_moscow_open_meteo()
    bot.send_message(message.chat.id, weather_info, reply_markup=make_main_kb())


@bot.message_handler(commands=['about'])
def about_cmd(message):
    keyboard = make_main_kb()
    bot.send_message(
        message.chat.id,
        "Это простой бот с примитивными командами и поддержкой OpenRouter AI, созданный с целью приобретения первых практических навыков в создании телеграмм ботов!\nАвтор бота: Седохин Даниил Алексеевич",
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


# ================  КОМАНДЫ OPENROUTER ================
@bot.message_handler(commands=["models"])
def cmd_models(message: types.Message) -> None:
    try:
        items = list_models()
        if not items:
            bot.reply_to(message, "Список моделей пуст.")
            return
        lines = ["Доступные модели:"]
        for m in items:
            star = "★" if m["active"] else " "
            lines.append(f"{star} {m['id']}. {m['label']}  [{m['key']}]")
        lines.append("\nАктивировать: /model <ID>")
        bot.reply_to(message, "\n".join(lines))
    except Exception as e:
        logging.error(f"Ошибка в /models: {e}")
        bot.reply_to(message, f"Ошибка: {e}")


@bot.message_handler(commands=["model"])
def cmd_model(message: types.Message) -> None:
    arg = message.text.replace("/model", "", 1).strip()

    if not arg:
        try:
            active = get_active_model()
            bot.reply_to(message,
                         text=f"Текущая активная модель: {active['label']} [{active['key']}]\n(сменить: /model <ID> или /models)")
        except Exception as e:
            bot.reply_to(message, text=f"Ошибка: {e}")
        return

    if not arg.isdigit():
        bot.reply_to(message, text="Использование: /model <ID из /models>")
        return

    try:
        active = set_active_model(int(arg))
        bot.reply_to(message, text=f"✅ Активная модель переключена: {active['label']} [{active['key']}]")
    except ValueError:
        bot.reply_to(message, text="❌ Неизвестный ID модели. Сначала /models.")
    except Exception as e:
        bot.reply_to(message, text=f"❌ Ошибка: {e}")


@bot.message_handler(commands=["ask"])
def cmd_ask(message: types.Message) -> None:
    q = message.text.replace("/ask", "", 1).strip()
    if not q:
        bot.reply_to(message, text="Использование: /ask <вопрос>\nПример: /ask Какая сегодня погода?")
        return

    try:
        model_key = get_active_model()["key"]
        bot.send_message(message.chat.id, "🤔 Думаю...")

        messages = [
            {"role": "system", "content": "Ты полезный ассистент. Отвечай кратко и по делу."},
            {"role": "user", "content": q[:1000]}
        ]

        text, ms = chat_once(messages, model=model_key, temperature=0.2, max_tokens=400)
        out = (text or "").strip()[:4000]

        response = f"{out}\n\n⏱️ {ms} мс | 🤖 {model_key}"
        bot.reply_to(message, response)

    except OpenRouterError as e:
        bot.reply_to(message, text=f"❌ Ошибка OpenRouter: {e}")
    except Exception as e:
        logging.error(f"Ошибка в /ask: {e}")
        bot.reply_to(message, text="❌ Непредвиденная ошибка при запросе к AI.")


@bot.message_handler(commands=["ask_model"])
def cmd_ask_model(message: types.Message) -> None:
    """Запрос к конкретной модели по ID без смены активной модели"""
    # Разбиваем команду: /ask_model ID вопрос
    parts = message.text.replace("/ask_model", "", 1).strip().split(maxsplit=1)

    if len(parts) < 2:
        bot.reply_to(message,
                     "Использование: /ask_model <ID> <вопрос>\n"
                     "Пример: /ask_model 7 Какая погода в Москве?\n"
                     "Список моделей: /models")
        return

    model_id_str, question = parts[0], parts[1].strip()

    # Проверяем ID модели
    if not model_id_str.isdigit():
        bot.reply_to(message, "❌ ID модели должен быть числом. Пример: /ask_model 3 Как дела?")
        return

    model_id = int(model_id_str)

    if not question:
        bot.reply_to(message, "❌ Вопрос не может быть пустым. Пример: /ask_model 5 Привет!")
        return

    try:
        # Получаем модель по ID
        model = get_model_by_id(model_id)
        model_key = model["key"]
        model_label = model["label"]

        bot.send_message(message.chat.id, f"🤔 Задаю вопрос модели {model_label}...")

        # Формируем сообщения для AI
        messages = [
            {"role": "system", "content": "Ты полезный ассистент. Отвечай кратко и по делу."},
            {"role": "user", "content": question[:1000]}
        ]

        # Выполняем запрос к указанной модели
        text, ms = chat_once(messages, model=model_key, temperature=0.2, max_tokens=400)
        out = (text or "").strip()[:4000]

        # Получаем активную модель для сравнения
        active_model = get_active_model()

        response = (
            f"{out}\n\n"
            f"⏱️ {ms} мс | 🤖 {model_label}\n"
            f"📋 ID модели: {model_id}"
        )

        # Если это не активная модель, добавляем примечание
        if model_id != active_model["id"]:
            response += f"\n⚠️ Это разовый запрос. Активная модель осталась: {active_model['label']}"

        bot.reply_to(message, response)

    except ValueError as e:
        bot.reply_to(message, f"❌ {str(e)}\nПроверьте список моделей: /models")
    except OpenRouterError as e:
        bot.reply_to(message, text=f"❌ Ошибка OpenRouter: {e}")
    except Exception as e:
        logging.error(f"Ошибка в /ask_model: {e}")
        bot.reply_to(message, text="❌ Непредвиденная ошибка при запросе к AI.")

# Обработчики для кнопок
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
    print("Бот запускается с поддержкой OpenRouter...")
    init_db()  # Инициализация базы данных
    bot.infinity_polling(skip_pending=True)