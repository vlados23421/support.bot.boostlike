import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("support.db")
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
    
    def close_ticket(self, ticket_id):
        self.cursor.execute(
            "UPDATE tickets SET status = 'closed' WHERE id = ?",
            (ticket_id,)
        )
        self.conn.commit()
