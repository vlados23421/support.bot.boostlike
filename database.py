import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="support.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
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
    
    def add_ticket(self, user_id, username, problem):
        self.cursor.execute(
            "INSERT INTO tickets (user_id, username, problem) VALUES (?, ?, ?)",
            (user_id, username, problem)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_tickets(self, status="open"):
        self.cursor.execute(
            "SELECT * FROM tickets WHERE status = ? ORDER BY id DESC",
            (status,)
        )
        return self.cursor.fetchall()
    
    def get_ticket_by_id(self, ticket_id):
        self.cursor.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (ticket_id,)
        )
        return self.cursor.fetchone()
    
    def close_ticket(self, ticket_id):
        self.cursor.execute(
            "UPDATE tickets SET status = 'closed' WHERE id = ?",
            (ticket_id,)
        )
        self.conn.commit()
    
    def add_feedback(self, user_id, rating, comment=""):
        self.cursor.execute(
            "INSERT INTO feedback (user_id, rating, comment) VALUES (?, ?, ?)",
            (user_id, rating, comment)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_stats(self):
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
    
    def close(self):
        self.conn.close()

db = Database()
