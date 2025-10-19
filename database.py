import sqlite3
import json
from datetime import datetime, date

DATABASE_FILE = "bot_data.db"

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        # Table for user data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                chat_id INTEGER PRIMARY KEY,
                language TEXT,
                last_update TEXT,
                tip_index INTEGER,
                horoscope_indices TEXT,
                is_new_user BOOLEAN
            )
        """)
        # Table for cache data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                last_update TEXT
            )
        """)
        conn.commit()

def save_user_data(chat_id: int, data: dict):
    """Saves user data to the database."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_data (chat_id, language, last_update, tip_index, horoscope_indices, is_new_user)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            chat_id,
            data.get("language"),
            str(data.get("last_update")),
            data.get("tip_index"),
            json.dumps(data.get("horoscope_indices")),
            data.get("is_new_user")
        ))
        conn.commit()

def load_user_data() -> dict:
    """Loads all user data from the database."""
    user_data = {}
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id, language, last_update, tip_index, horoscope_indices, is_new_user FROM user_data")
        rows = cursor.fetchall()
        for row in rows:
            chat_id, language, last_update_str, tip_index, horoscope_indices_str, is_new_user = row

            last_update = None
            if last_update_str and last_update_str != 'None':
                try:
                    last_update = datetime.strptime(last_update_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    pass # Keep it None if parsing fails

            horoscope_indices = {}
            if horoscope_indices_str:
                try:
                    horoscope_indices = json.loads(horoscope_indices_str)
                except (json.JSONDecodeError, TypeError):
                    pass # Keep it empty if parsing fails

            user_data[chat_id] = {
                "language": language,
                "last_update": last_update,
                "tip_index": tip_index,
                "horoscope_indices": horoscope_indices,
                "is_new_user": bool(is_new_user)
            }
    return user_data

def save_cache(key: str, value: dict):
    """Saves cache data to the database."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO cache (key, value, last_update)
            VALUES (?, ?, ?)
        """, (
            key,
            json.dumps(value, default=str),
            datetime.now().isoformat()
        ))
        conn.commit()

def load_cache(key: str) -> dict:
    """Loads cache data from the database."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM cache WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except (json.JSONDecodeError, TypeError):
                return {} # Return empty dict if parsing fails
    return {}
