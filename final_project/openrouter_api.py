# openrouter_api.py
import requests
import json
import time
import re
import os
from dotenv import load_dotenv

load_dotenv()

class OpenRouterNutrition:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        # Локальная база для запасного варианта
        self.local_db = {
            "овсянка": {"calories": 350, "protein": 12, "fat": 6, "carbs": 60},
            "творог": {"calories": 120, "protein": 18, "fat": 5, "carbs": 4},
            "куриная грудка": {"calories": 165, "protein": 31, "fat": 3.6, "carbs": 0},
            "гречка": {"calories": 130, "protein": 4.5, "fat": 1.3, "carbs": 27},
            "яйцо": {"calories": 70, "protein": 6, "fat": 5, "carbs": 0.6},
        }

        if self.api_key:
            print("✅ OpenRouter API инициализирован (модель: GPT-3.5-Turbo)")
        else:
            print("⚠️  OpenRouter API ключ не найден. Использую локальную базу.")

    def estimate_nutrition(self, food_text):
        """Получаем КБЖУ через OpenRouter или локальную базу"""

        # Сначала пробуем локальную базу
        result = self.local_db_estimate(food_text)
        if result and "source" in result:
            return result

        # Если есть API ключ и продукт не найден локально
        if self.api_key:
            return self.openrouter_estimate(food_text)
        else:
            # Нет ключа - используем запасной вариант
            return self.fallback_estimate(food_text)

    def local_db_estimate(self, food_text):
        """Поиск в локальной базе"""
        food_lower = food_text.lower()

        for food_name, data in self.local_db.items():
            if food_name in food_lower:
                # Извлекаем вес
                weight = self.extract_weight(food_lower)
                factor = weight / 100

                return {
                    "calories": int(data["calories"] * factor),
                    "protein_g": round(data["protein"] * factor, 1),
                    "fat_g": round(data["fat"] * factor, 1),
                    "carbs_g": round(data["carbs"] * factor, 1),
                    "advice": "Данные из локальной базы продуктов",
                    "confidence": "high",
                    "source": "local_db"
                }

        return {"confidence": "low"}

    def extract_weight(self, text):
        """Извлекает вес из текста"""
        patterns = [
            r'(\d+)\s*г\b',
            r'(\d+)\s*грамм',
            r'(\d+)\s*гр\b',
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))

        return 100  # стандартная порция

    def openrouter_estimate(self, food_text):
        """Получаем КБЖУ через OpenRouter API"""

        # Промпт для оценки питания
        messages = [
            {
                "role": "system",
                "content": """Ты профессиональный диетолог. Отвечай ТОЛЬКО в JSON:

{
  "calories": число,
  "protein_g": число,
  "fat_g": число,
  "carbs_g": число,
  "advice": "краткий совет на русском"
}

Если вес не указан - используй средние порции. Будь точным и реалистичным."""
            },
            {
                "role": "user",
                "content": f"Оцени КБЖУ для: {food_text}"
            }
        ]

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            data = {
                "model": "openai/gpt-3.5-turbo",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 500,
            }

            print(f"🤖 Отправляю запрос к OpenRouter: {food_text[:50]}...")

            start_time = time.time()
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response_time = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                print(f"❌ OpenRouter API error {response.status_code}")
                return self.fallback_estimate(food_text)

            result = response.json()

            if 'choices' not in result or not result['choices']:
                print("❌ Нет choices в ответе OpenRouter")
                return self.fallback_estimate(food_text)

            content = result['choices'][0]['message']['content'].strip()
            print(f"📨 Получен ответ за {response_time}мс: {content[:100]}...")

            # Парсим JSON
            parsed_data = self.parse_json_response(content)
            if parsed_data:
                parsed_data["source"] = "openrouter_gpt"
                return parsed_data
            else:
                return self.fallback_estimate(food_text)

        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка сети OpenRouter: {e}")
            return self.fallback_estimate(food_text)
        except Exception as e:
            print(f"❌ Ошибка OpenRouter: {e}")
            return self.fallback_estimate(food_text)

    def parse_json_response(self, text):
        """Парсим JSON из ответа"""
        # Очищаем от markdown
        text = text.replace('```json', '').replace('```', '').strip()

        # Ищем JSON
        start = text.find('{')
        end = text.rfind('}') + 1

        if start != -1 and end != 0:
            json_str = text[start:end]
            try:
                data = json.loads(json_str)
                # Проверяем обязательные поля
                required = ["calories", "protein_g", "fat_g", "carbs_g", "advice"]
                if all(field in data for field in required):
                    return data
            except json.JSONDecodeError:
                # Пытаемся исправить
                json_str = json_str.replace("'", '"')
                json_str = re.sub(r'(\w+):', r'"\1":', json_str)
                try:
                    return json.loads(json_str)
                except:
                    return None

        return None

    def fallback_estimate(self, food_text):
        """Запасной вариант если API не работает"""
        # Простая оценка по категориям
        food_lower = food_text.lower()

        if any(word in food_lower for word in ['каша', 'овсянк', 'гречк']):
            calories = 150
            advice = "Каши дают длительную энергию."
        elif any(word in food_lower for word in ['мясо', 'куриц', 'говядин']):
            calories = 180
            advice = "Мясо богато белком."
        elif any(word in food_lower for word in ['салат', 'овощ']):
            calories = 100
            advice = "Овощи содержат витамины."
        else:
            calories = 250
            advice = "Сбалансированное блюдо."

        # Корректируем по весу
        weight = self.extract_weight(food_lower)
        calories = int(calories * weight / 100)

        return {
            "calories": calories,
            "protein_g": round(calories * 0.2 / 4, 1),
            "fat_g": round(calories * 0.3 / 9, 1),
            "carbs_g": round(calories * 0.5 / 4, 1),
            "advice": f"{advice} (примерная оценка)",
            "source": "fallback_estimate"
        }

# Функция для тестирования
def test_openrouter():
    """Тестирование OpenRouter API"""
    from dotenv import load_dotenv
    import os

    load_dotenv()

    api_key = os.getenv('OPENROUTER_API_KEY')

    if not api_key:
        print("⚠️  OPENROUTER_API_KEY не найден в .env!")
        print("   Тестирую локальную базу...")

    try:
        api = OpenRouterNutrition(api_key)

        # Тестовые запросы
        test_cases = [
            "овсянка 100г с молоком",
            "куриная грудка",
            "салат из овощей"
        ]

        for test_case in test_cases:
            print(f"\n🔍 Тест: '{test_case}'")
            result = api.estimate_nutrition(test_case)
            print(f"   🔥 Калории: {result['calories']}")
            print(f"   📍 Источник: {result['source']}")
            print(f"   💡 Совет: {result['advice'][:50]}...")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    test_openrouter()