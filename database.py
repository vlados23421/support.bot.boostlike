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
                status TEXT DEFAULT 'Новая',
                answer TEXT,
                closed_at TEXT,
                rating INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица пользователей
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_blocked INTEGER DEFAULT 0
            )
        """)
        
        # Таблица отзывов
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
    
    # --- Заявки ---
    
    def add_ticket(self, user_id, username, problem):
        self.cursor.execute(
            "INSERT INTO tickets (user_id, username, problem) VALUES (?, ?, ?)",
            (user_id, username, problem)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_tickets(self, status=None):
        if status:
            self.cursor.execute(
                "SELECT * FROM tickets WHERE status = ? ORDER BY id DESC",
                (status,)
            )
        else:
            self.cursor.execute(
                "SELECT * FROM tickets WHERE status IN ('Новая', 'В работе') ORDER BY id DESC"
            )
        return self.cursor.fetchall()
    
    def get_ticket_by_id(self, ticket_id):
        self.cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        return self.cursor.fetchone()
    
    def get_all_tickets(self):
        self.cursor.execute("SELECT * FROM tickets ORDER BY id DESC")
        return self.cursor.fetchall()
    
    def close_ticket(self, ticket_id, answer=""):
        self.cursor.execute(
            "UPDATE tickets SET status = 'Закрыта', answer = ?, closed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (answer, ticket_id)
        )
        self.conn.commit()
    
    def update_ticket_status(self, ticket_id, status):
        self.cursor.execute(
            "UPDATE tickets SET status = ? WHERE id = ?",
            (status, ticket_id)
        )
        self.conn.commit()
    
    def search_tickets(self, query):
        self.cursor.execute(
            "SELECT * FROM tickets WHERE problem LIKE ? OR username LIKE ? ORDER BY id DESC",
            (f"%{query}%", f"%{query}%")
        )
        return self.cursor.fetchall()
    
    def get_user_tickets_count(self, user_id, date):
        self.cursor.execute(
            "SELECT COUNT(*) FROM tickets WHERE user_id = ? AND date(created_at) = ?",
            (user_id, date)
        )
        return self.cursor.fetchone()[0]
    
    # --- Пользователи ---
    
    def add_user(self, user_id, username, first_name, last_name=None):
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) 
                VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, last_name))
            self.conn.commit()
        except:
            pass
    
    def get_all_users(self):
        self.cursor.execute("SELECT user_id FROM users")
        return self.cursor.fetchall()
    
    def is_user_blocked(self, user_id):
        self.cursor.execute(
            "SELECT is_blocked FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = self.cursor.fetchone()
        return result and result[0] == 1
    
    def block_user(self, user_id):
        self.cursor.execute(
            "UPDATE users SET is_blocked = 1 WHERE user_id = ?",
            (user_id,)
        )
        self.conn.commit()
    
    def unblock_user(self, user_id):
        self.cursor.execute(
            "UPDATE users SET is_blocked = 0 WHERE user_id = ?",
            (user_id,)
        )
        self.conn.commit()
    
    # --- Отзывы ---
    
    def add_feedback(self, user_id, rating, comment=""):
        self.cursor.execute(
            "INSERT INTO feedback (user_id, rating, comment) VALUES (?, ?, ?)",
            (user_id, rating, comment)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    # --- Статистика ---
    
    def get_stats(self):
        self.cursor.execute("SELECT COUNT(*) FROM tickets")
        total_tickets = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT COUNT(*) FROM tickets WHERE status IN ('Новая', 'В работе')")
        open_tickets = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Закрыта'")
        closed_tickets = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT COUNT(*) FROM users")
        total_users = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT AVG(rating) FROM feedback")
        avg_rating = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute(
            "SELECT AVG((strftime('%s', closed_at) - strftime('%s', created_at)) / 60) FROM tickets WHERE status = 'Закрыта'"
        )
        avg_response = self.cursor.fetchone()[0] or 0
        
        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "closed_tickets": closed_tickets,
            "total_users": total_users,
            "avg_rating": avg_rating,
            "avg_response_time": avg_response
        }
    
    def close(self):
        self.conn.close()

db = Database()
