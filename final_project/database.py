#database.py
import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('data/food_diary.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Таблица записей о питании
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            food_text TEXT,
            calories INTEGER,
            protein_g REAL,
            fat_g REAL,
            carbs_g REAL,
            advice TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

        # Таблица дневных итогов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_totals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date DATE,
            total_calories INTEGER DEFAULT 0,
            total_protein REAL DEFAULT 0,
            total_fat REAL DEFAULT 0,
            total_carbs REAL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

        self.conn.commit()

    def add_user(self, user_id, username, first_name):
        """Добавляем пользователя в БД"""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name) 
        VALUES (?, ?, ?)
        ''', (user_id, username, first_name))
        self.conn.commit()

    def add_food_entry(self, user_id, food_text, nutrition_data):
        """Добавляем запись о приеме пищи"""
        cursor = self.conn.cursor()

        cursor.execute('''
        INSERT INTO food_entries 
        (user_id, food_text, calories, protein_g, fat_g, carbs_g, advice)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            food_text,
            nutrition_data['calories'],
            nutrition_data['protein_g'],
            nutrition_data['fat_g'],
            nutrition_data['carbs_g'],
            nutrition_data['advice']
        ))

        # Обновляем дневные итоги
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
        INSERT OR IGNORE INTO daily_totals (user_id, date) 
        VALUES (?, ?)
        ''', (user_id, today))

        cursor.execute('''
        UPDATE daily_totals 
        SET 
            total_calories = total_calories + ?,
            total_protein = total_protein + ?,
            total_fat = total_fat + ?,
            total_carbs = total_carbs + ?
        WHERE user_id = ? AND date = ?
        ''', (
            nutrition_data['calories'],
            nutrition_data['protein_g'],
            nutrition_data['fat_g'],
            nutrition_data['carbs_g'],
            user_id,
            today
        ))

        self.conn.commit()
        return cursor.lastrowid

    def get_today_summary(self, user_id):
        """Получаем итоги за сегодня"""
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')

        cursor.execute('''
        SELECT * FROM daily_totals 
        WHERE user_id = ? AND date = ?
        ''', (user_id, today))

        result = cursor.fetchone()

        if result:
            return {
                'total_calories': result[3],
                'total_protein': result[4],
                'total_fat': result[5],
                'total_carbs': result[6]
            }
        return None

    def get_today_entries(self, user_id):
        """Получаем все записи за сегодня"""
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')

        cursor.execute('''
        SELECT food_text, calories, protein_g, fat_g, carbs_g, advice, created_at
        FROM food_entries 
        WHERE user_id = ? AND DATE(created_at) = ?
        ORDER BY created_at
        ''', (user_id, today))

        return cursor.fetchall()

    def get_week_summary(self, user_id):
        """Получаем статистику за 7 дней"""
        cursor = self.conn.cursor()

        # Дата 7 дней назад
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        cursor.execute('''
        SELECT 
            date,
            total_calories,
            total_protein,
            total_fat,
            total_carbs
        FROM daily_totals 
        WHERE user_id = ? AND date >= ?
        ORDER BY date
        ''', (user_id, seven_days_ago))

        return cursor.fetchall()

    def get_month_summary(self, user_id):
        """Получаем статистику за 30 дней"""
        cursor = self.conn.cursor()

        # Дата 30 дней назад
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        cursor.execute('''
        SELECT 
            strftime('%Y-%m', date) as month,
            AVG(total_calories) as avg_calories,
            AVG(total_protein) as avg_protein,
            AVG(total_fat) as avg_fat,
            AVG(total_carbs) as avg_carbs,
            COUNT(*) as days_count
        FROM daily_totals 
        WHERE user_id = ? AND date >= ?
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month
        ''', (user_id, thirty_days_ago))

        return cursor.fetchall()

    def get_all_entries(self, user_id, limit=100):
        """Получаем все записи пользователя"""
        cursor = self.conn.cursor()

        cursor.execute('''
        SELECT 
            food_text,
            calories,
            protein_g,
            fat_g,
            carbs_g,
            created_at
        FROM food_entries 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        ''', (user_id, limit))

        return cursor.fetchall()

    def close(self):
        self.conn.close()