from datetime import datetime

def format_nutrition_response(nutrition_data, food_text):
    """Форматируем ответ с КБЖУ"""
    response = "🍽 *АНАЛИЗ ПРИЕМА ПИЩИ*\n"
    response += "═" * 35 + "\n\n"

    response += f"📋 *Что съели:*\n"
    response += f"`{food_text}`\n\n"

    response += f"📊 *ПИЩЕВАЯ ЦЕННОСТЬ:*\n"
    response += f"• 🔥 *Калории:* `{nutrition_data['calories']} ккал`\n"
    response += f"• 🥚 *Белки:* `{nutrition_data['protein_g']:.1f} г`\n"
    response += f"• 🥑 *Жиры:* `{nutrition_data['fat_g']:.1f} г`\n"
    response += f"• 🍚 *Углеводы:* `{nutrition_data['carbs_g']:.1f} г`\n\n"

    response += f"💡 *РЕКОМЕНДАЦИИ:*\n"
    response += f"_{nutrition_data['advice']}_\n\n"

    response += "✅ *Записано в дневник питания!*"

    return response


def format_daily_summary(summary_data, entries):
    """Форматируем дневную статистику с единым стилем"""
    if not summary_data:
        return "📅 *СЕГОДНЯ*\n═" * 20 + "\n\n📭 *Записей нет*\n\nИспользуйте ➕ Добавить еду чтобы начать!"

    response = "📅 *СЕГОДНЯ*\n"
    response += "═" * 35 + "\n\n"

    response += "📊 *СУММАРНЫЕ ПОКАЗАТЕЛИ:*\n"
    response += f"• 🔥 *Калории:* `{summary_data['total_calories']} ккал`\n"
    response += f"• 🥚 *Белки:* `{summary_data['total_protein']:.1f} г`\n"
    response += f"• 🥑 *Жиры:* `{summary_data['total_fat']:.1f} г`\n"
    response += f"• 🍚 *Углеводы:* `{summary_data['total_carbs']:.1f} г`\n\n"

    # Расчет процентов БЖУ
    total_nut = (summary_data['total_protein'] * 4 +
                 summary_data['total_fat'] * 9 +
                 summary_data['total_carbs'] * 4)

    if total_nut > 0:
        protein_pct = (summary_data['total_protein'] * 4 / total_nut) * 100
        fat_pct = (summary_data['total_fat'] * 9 / total_nut) * 100
        carbs_pct = (summary_data['total_carbs'] * 4 / total_nut) * 100

        response += "📈 *БАЛАНС БЖУ:*\n"
        response += f"• 🥚 Белки: `{protein_pct:.1f}%`\n"
        response += f"• 🥑 Жиры: `{fat_pct:.1f}%`\n"
        response += f"• 🍚 Углеводы: `{carbs_pct:.1f}%`\n\n"

    if entries:
        response += "🍽 *ПРИЕМЫ ПИЩИ:*\n"
        for i, entry in enumerate(entries, 1):
            food_text, calories, protein, fat, carbs, advice, time = entry
            time_str = datetime.strptime(time, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')

            response += f"\n{i}. *{time_str}* - {food_text}\n"
            response += f"   🔥 {calories} ккал | 🥚 {protein:.1f}г | 🥑 {fat:.1f}г | 🍚 {carbs:.1f}г\n"

    return response


def format_weekly_analysis(week_data):
    """Форматируем недельную статистику с единым стилем"""
    if not week_data:
        return "📈 *НЕДЕЛЯ*\n═" * 35 + "\n\n📭 *Недостаточно данных*\n\nДобавьте записи за последние 7 дней."

    # Подсчет статистик
    dates = []
    calories_list = []
    protein_list = []
    fat_list = []
    carbs_list = []

    for date_str, calories, protein, fat, carbs in week_data:
        dates.append(date_str)
        calories_list.append(calories or 0)
        protein_list.append(protein or 0)
        fat_list.append(fat or 0)
        carbs_list.append(carbs or 0)

    total_calories = sum(calories_list)
    avg_calories = sum(calories_list) / len(calories_list) if calories_list else 0
    max_calories = max(calories_list) if calories_list else 0
    min_calories = min(calories_list) if calories_list else 0

    response = "📈 *НЕДЕЛЯ*\n"
    response += "═" * 35 + "\n\n"

    response += f"📅 *Период:* {len(week_data)} дней\n\n"

    response += "🔥 *КАЛОРИИ:*\n"
    response += f"• Всего: `{total_calories:,} ккал`\n"
    response += f"• Среднее: `{avg_calories:.0f} ккал/день`\n"
    response += f"• Максимум: `{max_calories} ккал`\n"
    response += f"• Минимум: `{min_calories} ккал`\n\n"

    response += "🥗 *СРЕДНИЕ ПОКАЗАТЕЛИ В ДЕНЬ:*\n"
    response += f"• 🥚 Белки: `{sum(protein_list) / len(protein_list):.1f} г`\n"
    response += f"• 🥑 Жиры: `{sum(fat_list) / len(fat_list):.1f} г`\n"
    response += f"• 🍚 Углеводы: `{sum(carbs_list) / len(carbs_list):.1f} г`\n\n"

    # Дневная статистика
    response += "📊 *ПО ДНЯМ:*\n"
    for date_str, calories, protein, fat, carbs in week_data:
        date_formatted = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d.%m')
        response += f"\n• *{date_formatted}*:\n"
        response += f"  🔥 {calories} ккал | 🥚 {protein:.1f}г | 🥑 {fat:.1f}г | 🍚 {carbs:.1f}г"

    return response


def format_monthly_analysis(month_data):
    """Форматируем месячную статистику с единым стилем"""
    if not month_data:
        return "📅 *МЕСЯЦ*\n═" * 35 + "\n\n📭 *Недостаточно данных*\n\nДобавьте записи за последний месяц."

    response = "📅 *МЕСЯЦ*\n"
    response += "═" * 35 + "\n\n"

    for month, avg_cal, avg_prot, avg_fat, avg_carbs, days_count in month_data:
        month_name = datetime.strptime(month + "-01", "%Y-%m-%d").strftime("%B %Y")
        response += f"📅 *{month_name.upper()}* ({days_count} дней)\n"
        response += "─" * 30 + "\n\n"

        response += "📊 *СРЕДНИЕ ПОКАЗАТЕЛИ В ДЕНЬ:*\n"
        response += f"• 🔥 Калории: `{avg_cal:.0f} ккал`\n"
        response += f"• 🥚 Белки: `{avg_prot:.1f} г`\n"
        response += f"• 🥑 Жиры: `{avg_fat:.1f} г`\n"
        response += f"• 🍚 Углеводы: `{avg_carbs:.1f} г`\n\n"

        # Расчет процентов
        total_nut = (avg_prot * 4 + avg_fat * 9 + avg_carbs * 4)
        if total_nut > 0:
            protein_pct = (avg_prot * 4 / total_nut) * 100
            fat_pct = (avg_fat * 9 / total_nut) * 100
            carbs_pct = (avg_carbs * 4 / total_nut) * 100

            response += "📈 *БАЛАНС БЖУ:*\n"
            response += f"• 🥚 Белки: `{protein_pct:.1f}%`\n"
            response += f"• 🥑 Жиры: `{fat_pct:.1f}%`\n"
            response += f"• 🍚 Углеводы: `{carbs_pct:.1f}%`\n"

        response += "\n" + "═" * 35 + "\n\n"

    return response


def get_meal_time():
    """Определяем время приема пищи"""
    hour = datetime.now().hour

    if 5 <= hour < 11:
        return "завтрак 🍳"
    elif 11 <= hour < 16:
        return "обед 🍲"
    elif 16 <= hour < 22:
        return "ужин 🍽"
    else:
        return "ночной перекус 🌙"


def format_general_stats(all_entries, common_words):
    """Форматируем общую статистику с единым стилем"""
    response = "📊 *ОБЩАЯ СТАТИСТИКА*\n"
    response += "═" * 35 + "\n\n"

    response += f"📝 *Всего записей:* `{len(all_entries)}`\n\n"

    if common_words:
        response += "🍽 *ЧАСТЫЕ ПРОДУКТЫ:*\n"
        for word, count in common_words:
            response += f"• `{word}`: {count} раз\n"
        response += "\n"

    response += "📱 *ДОСТУПНЫЕ ОТЧЕТЫ:*\n"
    response += "• 📅 *Сегодня* - текущий день\n"
    response += "• 📈 *Неделя* - анализ за 7 дней\n"
    response += "• 📅 *Месяц* - сравнение по месяцам\n"
    response += "• 📊 *График* - визуализация данных"

    return response