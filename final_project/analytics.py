from datetime import datetime, timedelta
import statistics


class NutritionAnalytics:
    @staticmethod
    def get_weekly_analysis(week_data):
        """Анализ данных за неделю в едином стиле"""
        if not week_data:
            return "📭 *Недостаточно данных для анализа*"

        calories = [c for _, c, _, _, _ in week_data if c]
        protein = [p for _, _, p, _, _ in week_data if p]
        fat = [f for _, _, _, f, _ in week_data if f]
        carbs = [c for _, _, _, _, c in week_data if c]

        if not calories:
            return "📭 *Нет данных о калориях*"

        # Расчеты
        total_calories = sum(calories)
        avg_calories = statistics.mean(calories)
        max_calories = max(calories)
        min_calories = min(calories)

        # Формируем аналитику
        analysis = "\n📊 *АНАЛИТИКА НЕДЕЛИ*\n"
        analysis += "═" * 25 + "\n\n"

        analysis += "🔥 *СТАТИСТИКА КАЛОРИЙ:*\n"
        analysis += f"• Диапазон: `{min_calories} - {max_calories} ккал`\n"
        analysis += f"• Разброс: `{max_calories - min_calories} ккал`\n\n"

        if len(calories) >= 3:
            std_dev = statistics.stdev(calories)
            analysis += f"• Стандартное отклонение: `{std_dev:.0f} ккал`\n"
            if std_dev / avg_calories > 0.3:
                analysis += "  ⚠️  *Большой разброс в питании*\n"
            else:
                analysis += "  ✅ *Стабильное питание*\n"

        return analysis

    @staticmethod
    def get_trend_analysis(week_data):
        """Анализ трендов в едином стиле"""
        if len(week_data) < 3:
            return None

        calories = [c for _, c, _, _, _ in week_data]
        dates = [datetime.strptime(d, '%Y-%m-%d') for d, *_ in week_data]

        # Простой анализ тренда
        first_half_avg = statistics.mean(calories[:len(calories) // 2])
        second_half_avg = statistics.mean(calories[len(calories) // 2:])

        if second_half_avg > first_half_avg * 1.15:
            return "📈 *РАСТУЩИЙ ТРЕНД*\nКалорийность увеличивается"
        elif second_half_avg < first_half_avg * 0.85:
            return "📉 *НИСХОДЯЩИЙ ТРЕНД*\nКалорийность уменьшается"
        else:
            return "➡️  *СТАБИЛЬНЫЙ ТРЕНД*\nКалорийность стабильна"

    @staticmethod
    def get_recommendations(avg_calories, avg_protein, avg_fat, avg_carbs):
        """Генерация рекомендаций в едином стиле"""
        recommendations = "\n💡 *РЕКОМЕНДАЦИИ:*\n"
        recommendations += "═" * 25 + "\n\n"

        # Рекомендации по калориям
        if avg_calories < 1200:
            recommendations += "• ⚠️  *СЛИШКОМ МАЛО КАЛОРИЙ*\n  Рекомендуется увеличить потребление.\n\n"
        elif avg_calories > 3500:
            recommendations += "• ⚠️  *ВЫСОКОЕ ПОТРЕБЛЕНИЕ*\n  Рассмотрите уменьшение порций.\n\n"
        else:
            recommendations += "• ✅ *НОРМАЛЬНОЕ ПОТРЕБЛЕНИЕ*\n  Поддерживайте текущий уровень.\n\n"

        # Рекомендации по БЖУ
        if avg_protein < 50:
            recommendations += "• 🥚 *ДОБАВЬТЕ БЕЛКА*\n  Мясо, рыба, творог, яйца.\n\n"
        if avg_fat < 40:
            recommendations += "• 🥑 *ДОБАВЬТЕ ПОЛЕЗНЫХ ЖИРОВ*\n  Орехи, авокадо, оливковое масло.\n\n"
        if avg_carbs < 100:
            recommendations += "• 🍚 *ДОБАВЬТЕ СЛОЖНЫХ УГЛЕВОДОВ*\n  Крупы, цельнозерновые продукты.\n\n"

        return recommendations