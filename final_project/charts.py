#charts.py
import matplotlib.pyplot as plt
import io
from datetime import datetime


class NutritionCharts:
    @staticmethod
    def create_weekly_chart(week_data):
        """Создает график за неделю"""
        if not week_data:
            return None

        try:
            # Подготовка данных
            dates = []
            calories = []
            proteins = []
            fats = []
            carbs = []

            for date_str, cal, prot, fat, carb in week_data:
                try:
                    # Конвертируем дату
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    dates.append(date_obj.strftime('%d.%m'))
                    calories.append(cal if cal is not None else 0)
                    proteins.append(prot if prot is not None else 0)
                    fats.append(fat if fat is not None else 0)
                    carbs.append(carb if carb is not None else 0)
                except Exception as e:
                    print(f"Ошибка обработки данных: {e}")
                    continue

            if len(dates) < 2:
                return None

            # Настройка стиля
            plt.style.use('seaborn-v0_8-darkgrid')

            # Создаем график с 2 подграфиками
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            fig.patch.set_facecolor('#f5f5f5')

            # График 1: Калории (линейный)
            ax1.plot(dates, calories, 'o-', linewidth=3, markersize=10,
                     color='#ff6b6b', markerfacecolor='white', markeredgewidth=2)
            ax1.set_title('🔥 Калории за неделю', fontsize=16, fontweight='bold', pad=15)
            ax1.set_ylabel('Ккал', fontsize=12)
            ax1.grid(True, alpha=0.4)
            ax1.set_facecolor('#fafafa')

            # Добавляем значение над точками
            for i, (date, cal) in enumerate(zip(dates, calories)):
                ax1.annotate(f'{cal:.0f}', (i, cal),
                             textcoords="offset points",
                             xytext=(0, 10), ha='center', fontsize=10)

            # График 2: БЖУ (столбчатая диаграмма)
            width = 0.2
            x = range(len(dates))
            colors = ['#4ecdc4', '#ffd166', '#06d6a0']  # Синий, оранжевый, зеленый

            bars1 = ax2.bar([i - width for i in x], proteins, width,
                            label='🥚 Белки', color=colors[0], edgecolor='white', linewidth=1.5)
            bars2 = ax2.bar(x, fats, width,
                            label='🥑 Жиры', color=colors[1], edgecolor='white', linewidth=1.5)
            bars3 = ax2.bar([i + width for i in x], carbs, width,
                            label='🍚 Углеводы', color=colors[2], edgecolor='white', linewidth=1.5)

            ax2.set_title('🥗 БЖУ за неделю', fontsize=16, fontweight='bold', pad=15)
            ax2.set_ylabel('Граммы', fontsize=12)
            ax2.set_xticks(x)
            ax2.set_xticklabels(dates, rotation=0)
            ax2.legend(loc='upper left', fontsize=11)
            ax2.grid(True, alpha=0.4, axis='y')
            ax2.set_facecolor('#fafafa')

            # Добавляем подписи значений
            def autolabel(bars):
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax2.annotate(f'{height:.0f}',
                                     xy=(bar.get_x() + bar.get_width() / 2, height),
                                     xytext=(0, 3),
                                     textcoords="offset points",
                                     ha='center', va='bottom', fontsize=9)

            autolabel(bars1)
            autolabel(bars2)
            autolabel(bars3)

            # Настройка layout
            plt.tight_layout(pad=3.0)

            # Конвертируем в байты
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                        facecolor=fig.get_facecolor(), edgecolor='none')
            buf.seek(0)
            plt.close(fig)

            return buf

        except Exception as e:
            print(f"Ошибка создания графика: {e}")
            plt.close('all')
            return None

    @staticmethod
    def create_daily_chart(day_data):
        """Создает круговую диаграмму за день"""
        if not day_data:
            return None

        try:
            # day_data: (calories, protein, fat, carbs)
            calories = day_data[0] or 0
            protein = day_data[1] or 0
            fat = day_data[2] or 0
            carbs = day_data[3] or 0

            # Расчет процентов
            total = protein + fat + carbs
            if total == 0:
                return None

            sizes = [protein, fat, carbs]
            labels = [f'Белки\n{protein:.1f}г', f'Жиры\n{fat:.1f}г', f'Углеводы\n{carbs:.1f}г']
            colors = ['#4ecdc4', '#ffd166', '#06d6a0']
            explode = (0.05, 0.05, 0.05)

            # Создаем круговую диаграмму
            fig, ax = plt.subplots(figsize=(8, 8))

            wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                              autopct='%1.1f%%', shadow=True, startangle=90,
                                              textprops={'fontsize': 11})

            # Настройка стиля
            ax.set_title(f'📊 Распределение БЖУ\n🔥 {calories:.0f} ккал',
                         fontsize=16, fontweight='bold', pad=20)

            # Делаем проценты жирными
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')

            plt.tight_layout()

            # Конвертируем в байты
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                        facecolor=fig.get_facecolor(), edgecolor='none')
            buf.seek(0)
            plt.close(fig)

            return buf

        except Exception as e:
            print(f"Ошибка создания круговой диаграммы: {e}")
            plt.close('all')
            return None