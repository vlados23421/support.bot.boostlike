import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="support.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Таблица заявок
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                problem TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица пользователей (для статистики)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_activity TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица для отзывов/оценок (опционально)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                rating INTEGER,
                comment TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    # --- Работа с заявками ---
    
    def add_ticket(self, user_id, username, problem):
        """Создать новую заявку"""
        self.cursor.execute(
            "INSERT INTO tickets (user_id, username, problem) VALUES (?, ?, ?)",
            (user_id, username, problem)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_tickets(self, status="open"):
        """Получить все заявки по статусу"""
        self.cursor.execute(
            "SELECT * FROM tickets WHERE status = ? ORDER BY id DESC",
            (status,)
        )
        return self.cursor.fetchall()
    
    def get_ticket_by_id(self, ticket_id):
        """Получить заявку по ID"""
        self.cursor.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (ticket_id,)
        )
        return self.cursor.fetchone()
    
    def get_user_tickets(self, user_id, status="open"):
        """Получить заявки пользователя"""
        self.cursor.execute(
            "SELECT * FROM tickets WHERE user_id = ? AND status = ? ORDER BY id DESC",
            (user_id, status)
        )
        return self.cursor.fetchall()
    
    def close_ticket(self, ticket_id):
        """Закрыть заявку"""
        self.cursor.execute(
            "UPDATE tickets SET status = 'closed' WHERE id = ?",
            (ticket_id,)
        )
        self.conn.commit()
    
    def reopen_ticket(self, ticket_id):
        """Открыть заявку заново"""
        self.cursor.execute(
            "UPDATE tickets SET status = 'open' WHERE id = ?",
            (ticket_id,)
        )
        self.conn.commit()
    
    def delete_ticket(self, ticket_id):
        """Удалить заявку"""
        self.cursor.execute(
            "DELETE FROM tickets WHERE id = ?",
            (ticket_id,)
        )
        self.conn.commit()
    
    def get_all_tickets(self, limit=50):
        """Получить все заявки (для статистики)"""
        self.cursor.execute(
            "SELECT * FROM tickets ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()
    
    # --- Работа с пользователями ---
    
    def add_user(self, user_id, username, first_name, last_name=None):
        """Зарегистрировать пользователя"""
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) 
                VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, last_name))
            
            # Обновляем активность
            self.cursor.execute(
                "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            self.conn.commit()
            return True
        except:
            return False
    
    def get_user(self, user_id):
        """Получить данные пользователя"""
        self.cursor.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        return self.cursor.fetchone()
    
    def get_all_users(self):
        """Получить всех пользователей"""
        self.cursor.execute("SELECT * FROM users ORDER BY registered_at DESC")
        return self.cursor.fetchall()
    
    def get_users_count(self):
        """Количество пользователей"""
        self.cursor.execute("SELECT COUNT(*) FROM users")
        return self.cursor.fetchone()[0]
    
    # --- Работа с отзывами ---
    
    def add_feedback(self, user_id, rating, comment=""):
        """Добавить отзыв"""
        self.cursor.execute(
            "INSERT INTO feedback (user_id, rating, comment) VALUES (?, ?, ?)",
            (user_id, rating, comment)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_feedback(self, limit=10):
        """Получить последние отзывы"""
        self.cursor.execute(
            "SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()
    
    # --- Статистика ---
    
    def get_stats(self):
        """Получить общую статистику"""
        self.cursor.execute("SELECT COUNT(*) FROM tickets")
        total_tickets = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'")
        open_tickets = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'closed'")
        closed_tickets = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM users")
        total_users = self.cursor.fetchone()[0]
        
        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "closed_tickets": closed_tickets,
            "total_users": total_users
        }
    
    # --- Очистка ---
    
    def clear_closed_tickets(self, days=30):
        """Удалить закрытые заявки старше N дней"""
        self.cursor.execute(
            "DELETE FROM tickets WHERE status = 'closed' AND created_at < datetime('now', ?)",
            (f"-{days} days",)
        )
        self.conn.commit()
        return self.cursor.rowcount
    
    def close(self):
        """Закрыть соединение с БД"""
        self.conn.close()

# Создаем экземпляр БД
db = Database()
