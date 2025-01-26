import sqlite3
from datetime import datetime
import json

class Database:
    def __init__(self, db_file="app.db"):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_file)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # General queries history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    model TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    response JSON NOT NULL,
                    email_sent BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Weather queries history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weather_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    city TEXT NOT NULL,
                    state TEXT NOT NULL,
                    weather_data JSON NOT NULL,
                    image_url TEXT
                )
            ''')
            
            # Database schema generation history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schema_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    description TEXT NOT NULL,
                    schema_data JSON NOT NULL,
                    sample_data JSON NOT NULL
                )
            ''')
            
            # Token usage tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    request_type TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    estimated_cost REAL NOT NULL
                )
            ''')
            
            # Flashcards history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flashcards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    flashcards TEXT
                )
            ''')
            
            conn.commit()

    def save_query(self, model, prompt, response, email_sent=False):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO query_history (timestamp, model, prompt, response, email_sent)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now(), model, prompt, json.dumps(response), email_sent))
            return cursor.lastrowid

    def save_weather_query(self, city, state, weather_data, image_url):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO weather_history (timestamp, city, state, weather_data, image_url)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now(), city, state, json.dumps(weather_data), image_url))
            return cursor.lastrowid

    def save_schema_query(self, description, schema_data, sample_data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO schema_history (timestamp, description, schema_data, sample_data)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now(), description, json.dumps(schema_data), json.dumps(sample_data)))
            return cursor.lastrowid

    def save_token_usage(self, request_type, model, prompt_tokens, completion_tokens, total_tokens, estimated_cost):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO token_usage (timestamp, request_type, model, prompt_tokens, 
                                       completion_tokens, total_tokens, estimated_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), request_type, model, prompt_tokens, 
                  completion_tokens, total_tokens, estimated_cost))
            return cursor.lastrowid

    def save_flashcards(self, flashcards):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO flashcards (timestamp, flashcards)
                VALUES (?, ?)
            ''', (datetime.now(), json.dumps(flashcards)))
            conn.commit()

    def get_query_history(self, limit=50):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM query_history 
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

    def get_weather_history(self, limit=50):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM weather_history 
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

    def get_schema_history(self, limit=50):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM schema_history 
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

    def get_token_usage(self, limit=100):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM token_usage 
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

    def get_flashcard_history(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, flashcards FROM flashcards ORDER BY timestamp DESC LIMIT 100
            ''')
            return cursor.fetchall() 