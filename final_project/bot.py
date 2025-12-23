# bot.py
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from utils import (
    format_nutrition_response,
    format_daily_summary,
    format_weekly_analysis,
    format_monthly_analysis,
    format_general_stats,
    get_meal_time
)
from analytics import NutritionAnalytics
from collections import Counter
from charts import NutritionCharts
from config import TELEGRAM_TOKEN
from openrouter_api import OpenRouterNutrition
from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация
db = Database()
nutrition_api = OpenRouterNutrition()

# Состояния для ConversationHandler
WAITING_FOOD_INPUT = 1

# Клавиатура с кнопками
def create_main_keyboard():
    """Создает основную клавиатуру"""
    keyboard = [
        [KeyboardButton("➕ Добавить еду"), KeyboardButton("📊 Сегодня")],
        [KeyboardButton("📈 Неделя"), KeyboardButton("📅 Месяц")],
        [KeyboardButton("📊 График"), KeyboardButton("🆘 Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = [[KeyboardButton("❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ================================ КОМАНДЫ БОТА ====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    # Добавляем пользователя в БД
    db.add_user(user.id, user.username, user.first_name)

    welcome_message = f"""
🍎 *Привет, {user.first_name}!* 

Я - ваш умный помощник по питанию! 🥗

*Что я умею:*
✅ Анализировать приемы пищи через нейросеть
✅ Подсчитывать КБЖУ (калории, белки, жиры, углеводы)
✅ Давать советы по питанию
✅ Строить график КБЖУ, основанный на вашем питании
✅ Вести дневник питания

*Просто нажмите кнопки ниже:* 👇

➕ *Добавить еду* - записать прием пищи
📊 *Сегодня* - статистика за день
📈 *Неделя* - статистика за неделю
📅 *Месяц* - статистика за месяц
📊 *График* - график КБЖУ
🆘 *Помощь* - справка по командам

*Или используйте команды:*
`/add [еда]` - быстрый ввод
`/today` - сегодняшняя статистика
`/week` - недельная статистика
`/month` - статистика за месяц
`/chart` - график КБЖУ
`/start` - вводное сообщение
`/help` - помощь

*Примеры:*
• `овсянка 100г на молоке`
• `куриная грудка 150г с гречкой`
• `салат и кофе`
"""

    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


async def add_food_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Добавить еду'"""
    await update.message.reply_text(
        "🍽 *Что вы съели?*\n\n"
        "📝 *Примеры:*\n"
        "• овсянка 100г на молоке\n"
        "• куриная грудка с гречкой\n"
        "• яблоко и творог 200г\n\n"
        "Просто напишите что вы съели и нажмите отправить!\n"
        "Используйте *❌ Отмена* чтобы вернуться в меню.",
        parse_mode='Markdown',
        reply_markup=create_cancel_keyboard()
    )

    return WAITING_FOOD_INPUT


async def handle_food_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода еды (после нажатия кнопки)"""
    food_text = update.message.text.strip()

    # Проверяем, не нажата ли кнопка отмены
    if food_text == "❌ Отмена":
        await update.message.reply_text(
            "❌ Добавление отменено.",
            reply_markup=create_main_keyboard()
        )
        return ConversationHandler.END

    user = update.effective_user

    # Отправляем сообщение о начале анализа
    try:
        processing_msg = await update.message.reply_text(
            f"🔍 *Анализирую {get_meal_time()}...*\n"
            f"`{food_text}`\n\n"
            f"⏳ Ведем подсчет КБЖУ...",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        processing_msg = None

    try:
        # Получаем данные от OpenRouter или локальной базы
        nutrition_data = nutrition_api.estimate_nutrition(food_text)

        # Сохраняем в БД
        db.add_food_entry(user.id, food_text, nutrition_data)

        # Форматируем ответ
        response = format_nutrition_response(nutrition_data, food_text)

        # Добавляем информацию об источнике
        if "source" in nutrition_data:
            source_info = {
                "openrouter_gpt": "🤖 Анализ от нейросети GPT-3.5",
                "local_db": "📊 Данные из локальной базы",
                "fallback_estimate": "⚖️ Примерная оценка"
            }
            source_text = source_info.get(nutrition_data["source"], "")
            if source_text:
                response += f"\n\n{source_text}"

        # Обновляем сообщение с результатом
        if processing_msg:
            try:
                await processing_msg.edit_text(response, parse_mode='Markdown')
            except:
                await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.message.reply_text(response, parse_mode='Markdown')

        # Предлагаем добавить еще или вернуться в меню
        await update.message.reply_text(
            "✅ *Готово!*\n\n"
            "Хотите добавить еще один прием пищи?\n"
            "Напишите что съели или нажмите *❌ Отмена* чтобы вернуться в меню.",
            parse_mode='Markdown',
            reply_markup=create_cancel_keyboard()
        )

        # Остаемся в том же состоянии (можно добавить еще еду)
        return WAITING_FOOD_INPUT

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        error_msg = "❌ *Произошла ошибка*\nПопробуйте еще раз или опишите прием пищи подробнее."

        if processing_msg:
            try:
                await processing_msg.edit_text(error_msg, parse_mode='Markdown')
            except:
                await update.message.reply_text(error_msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(error_msg, parse_mode='Markdown')

        return WAITING_FOOD_INPUT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    await update.message.reply_text(
        "✅ Операция отменена.",
        reply_markup=create_main_keyboard()
    )
    return ConversationHandler.END


async def add_food_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /add (оставляем для совместимости)"""
    if not context.args:
        await update.message.reply_text(
            "🍎 *Укажите что вы съели*\n\n"
            "Примеры:\n"
            "• `/add овсянка 100г на молоке`\n"
            "• `/add куриная грудка с гречкой`\n"
            "• `/add салат и кофе`",
            parse_mode='Markdown',
            reply_markup=create_main_keyboard()
        )
        return

    food_text = ' '.join(context.args)
    user = update.effective_user

    # Отправляем сообщение о начале анализа
    processing_msg = await update.message.reply_text(
        f"🔍 *Анализирую {get_meal_time()}...*\n"
        f"`{food_text}`\n\n"
        f"⏳ Ведем подсчет КБЖУ...",
        parse_mode='Markdown'
    )

    try:
        # Получаем данные от OpenRouter или локальной базы
        nutrition_data = nutrition_api.estimate_nutrition(food_text)

        # Сохраняем в БД
        db.add_food_entry(user.id, food_text, nutrition_data)

        # Форматируем ответ
        response = format_nutrition_response(nutrition_data, food_text)

        # Добавляем информацию об источнике
        if "source" in nutrition_data:
            source_info = {
                "openrouter_gpt": "🤖 Анализ от нейросети GPT-3.5",
                "local_db": "📊 Данные из локальной базы",
                "fallback_estimate": "⚖️ Примерная оценка"
            }
            source_text = source_info.get(nutrition_data["source"], "")
            if source_text:
                response += f"\n\n{source_text}"

        # Обновляем сообщение с результатом
        await processing_msg.edit_text(
            response,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await processing_msg.edit_text(
            "❌ *Произошла ошибка*\n"
            "Попробуйте еще раз или опишите прием пищи подробнее.",
            parse_mode='Markdown'
        )


async def today_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Сегодня'"""
    user = update.effective_user

    # Получаем данные из БД
    summary = db.get_today_summary(user.id)
    entries = db.get_today_entries(user.id)

    # Форматируем ответ
    response = format_daily_summary(summary, entries)

    await update.message.reply_text(
        response,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Общая статистика"""
    user = update.effective_user

    # Получаем все записи
    all_entries = db.get_all_entries(user.id, limit=50)

    if not all_entries:
        await update.message.reply_text(
            "📊 *ОБЩАЯ СТАТИСТИКА*\n═" * 18 + "\n\n📭 *У вас еще нет записей*\n\nНачните с добавления первого приема пищи!",
            parse_mode='Markdown',
            reply_markup=create_main_keyboard()
        )
        return

    # Анализ самых частых продуктов
    food_words = []
    for food_text, _, _, _, _, _ in all_entries:
        words = food_text.lower().split()
        food_words.extend([w for w in words if len(w) > 2])

    common_words = Counter(food_words).most_common(5)

    # Форматируем ответ
    response = format_general_stats(all_entries, common_words)

    await update.message.reply_text(
        response,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Помощь'"""
    await update.message.reply_text(
        "🆘 *Помощь*\n\n"
        "*Как пользоваться:*\n"
        "1. Нажмите *➕ Добавить еду*\n"
        "2. Напишите что съели (например: 'овсянка 100г с ягодами')\n"
        "3. Получите анализ КБЖУ и совет\n"
        "4. Получайте графики вашего КБЖУ\n"
        "5. Просматривайте статистику за день/неделю/месяц\n\n"
        "*Примеры ввода:*\n"
        "• овсянка 100г с молоком\n"
        "• курица 150г + рис 100г\n"
        "• творог 200г и банан\n"
        "• яблоко, кофе\n"
        "• салат из овощей\n\n"
        "*Советы:*\n"
        "• Указывайте примерный вес для точности\n"
        "• Используйте *📊 Сегодня* для контроля\n"
        "• Добавляйте каждый прием пищи",
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


async def handle_other_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик других сообщений"""
    text = update.message.text

    # Если сообщение не команда и не кнопка
    if not text.startswith('/'):
        # Предлагаем использовать кнопки
        await update.message.reply_text(
            "🤔 *Я вас не понял*\n\n"
            "Используйте кнопки ниже или команды:\n"
            "• *➕ Добавить еду* - записать прием пищи\n"
            "• *📊 Сегодня* - статистика за день\n"
            "• *🆘 Помощь* - справка\n\n"
            "Или напишите `/help` для справки.",
            parse_mode='Markdown',
            reply_markup=create_main_keyboard()
        )


async def week_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика за неделю"""
    user = update.effective_user

    # Получаем данные за неделю
    week_data = db.get_week_summary(user.id)

    # Форматируем ответ
    response = format_weekly_analysis(week_data)

    # Добавляем аналитику, если есть данные
    if week_data and len(week_data) >= 3:
        try:
            analysis = NutritionAnalytics.get_weekly_analysis(week_data)
            trend = NutritionAnalytics.get_trend_analysis(week_data)
            if trend:
                response += f"\n\n📈 *ТРЕНДЫ:*\n{trend}"
        except:
            pass

    await update.message.reply_text(
        response,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


async def month_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика за месяц"""
    user = update.effective_user

    # Получаем данные за месяц
    month_data = db.get_month_summary(user.id)

    # Форматируем ответ
    response = format_monthly_analysis(month_data)

    await update.message.reply_text(
        response,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


async def show_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать график за неделю"""
    user = update.effective_user

    # Получаем данные за неделю
    week_data = db.get_week_summary(user.id)

    if not week_data or len(week_data) < 2:
        await update.message.reply_text(
            "📊 *Недостаточно данных для графика*\n\n"
            "Нужно минимум 2 дня записей.\n"
            "Используйте *➕ Добавить еду* чтобы заполнить дневник!",
            parse_mode='Markdown',
            reply_markup=create_main_keyboard()
        )
        return

    # Сообщение о создании графика
    processing_msg = await update.message.reply_text(
        "🎨 *Создаю график...*\n⏳ Это займет несколько секунд",
        parse_mode='Markdown'
    )

    try:
        # Создаем график
        chart_buffer = NutritionCharts.create_weekly_chart(week_data)

        if chart_buffer:
            # Удаляем сообщение об обработке
            try:
                await processing_msg.delete()
            except:
                pass

            # Отправляем график
            await update.message.reply_photo(
                photo=chart_buffer,
                caption="📈 *Ваша статистика за неделю*\n\n"
                        "• 🔴 Линия - калории\n"
                        "• 🔵 Синий - белки\n"
                        "• 🟠 Оранжевый - жиры\n"
                        "• 🟢 Зеленый - углеводы\n\n"
                        "Добавляйте записи каждый день для более точной статистики!",
                parse_mode='Markdown',
                reply_markup=create_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ *Не удалось создать график*",
                parse_mode='Markdown',
                reply_markup=create_main_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка создания графика: {e}")
        await update.message.reply_text(
            f"❌ *Ошибка создания графика:*\n{str(e)[:100]}",
            parse_mode='Markdown',
            reply_markup=create_main_keyboard()
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке сообщения: {context.error}")

    # Отправляем сообщение пользователю только если есть update
    if update and hasattr(update, 'effective_user'):
        try:
            error_msg = (
                "⚠️ *Произошла ошибка*\n\n"
                "Попробуйте выполнить действие еще раз или используйте команду /start для перезагрузки."
            )

            # Проверяем, есть ли сообщение для ответа
            if update.message:
                await update.message.reply_text(
                    error_msg,
                    parse_mode='Markdown',
                    reply_markup=create_main_keyboard()
                )
            elif update.callback_query:
                await update.callback_query.message.reply_text(
                    error_msg,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")

    return

def main():
    """Запуск бота"""

    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # ConversationHandler для добавления еды
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^➕ Добавить еду$'), add_food_button),
            CommandHandler('add', add_food_command)
        ],
        states={
            WAITING_FOOD_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_food_input)
            ]
        },
        fallbacks=[
            MessageHandler(filters.Regex('^❌ Отмена$'), cancel),
            CommandHandler('cancel', cancel),
            CommandHandler('start', start)
        ]
    )

    # Регистрируем обработчики
    application.add_handler(conv_handler)

    # Обработчики кнопок
    application.add_handler(MessageHandler(filters.Regex('^📊 Сегодня$'), today_summary))
    application.add_handler(MessageHandler(filters.Regex('^📈 Статистика$'), stats_command))
    application.add_handler(MessageHandler(filters.Regex('^🆘 Помощь$'), help_command))
    application.add_handler(MessageHandler(filters.Regex('^📈 Неделя$'), week_stats))
    application.add_handler(MessageHandler(filters.Regex('^📅 Месяц$'), month_stats))
    application.add_handler(MessageHandler(filters.Regex('^📊 График$'), show_chart))

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", today_summary))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("week", week_stats))
    application.add_handler(CommandHandler("month", month_stats))
    application.add_handler(CommandHandler("chart", show_chart))

    # Обработчик всех остальных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_other_messages))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    # Запуск бота
    print("🤖 Бот запущен!")
    print("🔧 Используется OpenRouter API (GPT-3.5 Turbo)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()