"""
Database Manager for AI Companion Plant Widget
Handles SQLite3 persistence for plant state, chat history, and user profile.
"""
import sqlite3
import os
import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
from .config import get_base_dir

class DatabaseManager:
    def __init__(self, db_filename: str = "plant_data.db"):
        self.db_path = os.path.join(get_base_dir(), db_filename)
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        """Initialize required database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. plant_state table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plant_state (
                    id INTEGER PRIMARY KEY,
                    water INTEGER NOT NULL DEFAULT 80,
                    sunlight INTEGER NOT NULL DEFAULT 80,
                    affection INTEGER NOT NULL DEFAULT 20,
                    stage INTEGER NOT NULL DEFAULT 1,
                    exp INTEGER NOT NULL DEFAULT 0,
                    total_interactions INTEGER NOT NULL DEFAULT 0,
                    species TEXT NOT NULL DEFAULT 'classic',
                    created_at TIMESTAMP,
                    last_updated TIMESTAMP NOT NULL
                )
            """)

            # Ensure species column exists if migrated from old db
            try:
                cursor.execute("ALTER TABLE plant_state ADD COLUMN species TEXT NOT NULL DEFAULT 'classic'")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE plant_state ADD COLUMN created_at TIMESTAMP")
            except sqlite3.OperationalError:
                pass

            # 2. chat_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                )
            """)

            # 3. user_profile table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # 4. graduated_plants (Garden Collection) table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS graduated_plants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    species TEXT NOT NULL,
                    graduated_at TIMESTAMP NOT NULL,
                    total_interactions INTEGER NOT NULL DEFAULT 0
                )
            """)

            # 5. achievements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id TEXT PRIMARY KEY,
                    unlocked_at TIMESTAMP NOT NULL
                )
            """)

            # 6. daily_fortunes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_fortunes (
                    date TEXT PRIMARY KEY,
                    message TEXT NOT NULL
                )
            """)

            # 7. mood_history (Mental Wellness / Mood Trends) table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mood_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    date TEXT NOT NULL,
                    mood_type TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    snippet TEXT
                )
            """)

            # 8. lifetime_stats (Action counters for achievements) table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lifetime_stats (
                    key TEXT PRIMARY KEY,
                    value INTEGER NOT NULL DEFAULT 0
                )
            """)

            # Insert initial state if not present
            cursor.execute("SELECT COUNT(*) FROM plant_state WHERE id = 1")
            if cursor.fetchone()[0] == 0:
                now_str = datetime.datetime.now().isoformat()
                cursor.execute("""
                    INSERT INTO plant_state (id, water, sunlight, affection, stage, exp, total_interactions, species, created_at, last_updated)
                    VALUES (1, 80, 80, 20, 1, 0, 0, 'classic', ?, ?)
                """, (now_str, now_str))

            conn.commit()

    def load_plant_state(self) -> Dict[str, Any]:
        """Load the latest plant state."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM plant_state WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return dict(row)
            # Default fallback
            now_str = datetime.datetime.now().isoformat()
            return {
                "id": 1,
                "water": 80,
                "sunlight": 80,
                "affection": 20,
                "stage": 1,
                "exp": 0,
                "total_interactions": 0,
                "species": "classic",
                "created_at": now_str,
                "last_updated": now_str
            }

    def save_plant_state(self, state: Dict[str, Any]):
        """Save the updated plant state, preserving last_updated timestamp if provided."""
        last_updated = state.get("last_updated") or datetime.datetime.now().isoformat()
        created_at = state.get("created_at") or datetime.datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE plant_state
                SET water = ?,
                    sunlight = ?,
                    affection = ?,
                    stage = ?,
                    exp = ?,
                    total_interactions = ?,
                    species = ?,
                    created_at = ?,
                    last_updated = ?
                WHERE id = 1
            """, (
                int(state.get("water", 80)),
                int(state.get("sunlight", 80)),
                int(state.get("affection", 20)),
                int(state.get("stage", 1)),
                int(state.get("exp", 0)),
                int(state.get("total_interactions", 0)),
                str(state.get("species", "classic")),
                created_at,
                last_updated
            ))
            conn.commit()

    def add_chat_message(self, role: str, content: str):
        """Append a message to chat history."""
        now_str = datetime.datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_history (role, content, timestamp)
                VALUES (?, ?, ?)
            """, (role, content, now_str))
            conn.commit()

    def get_recent_chat_history(self, limit: int = 6) -> List[Dict[str, str]]:
        """Sliding Window: Fetch recent messages."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content FROM chat_history
                ORDER BY id DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            history = [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
            return history

    def clear_chat_history(self):
        """Clear all conversation logs."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history")
            conn.commit()

    def get_profile_value(self, key: str, default: str = "") -> str:
        """Fetch profile entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_profile WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_profile_value(self, key: str, value: str):
        """Set or update profile entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_profile (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))
            conn.commit()

    # --- Garden & Graduation ---
    def graduate_plant(self, name: str, species: str, total_interactions: int):
        """Register completed plant to Garden collection."""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO graduated_plants (name, species, graduated_at, total_interactions)
                VALUES (?, ?, ?, ?)
            """, (name, species, now_str, total_interactions))
            conn.commit()

    def get_graduated_plants(self) -> List[Dict[str, Any]]:
        """Fetch all graduated plants in the garden."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, species, graduated_at, total_interactions
                FROM graduated_plants ORDER BY id DESC
            """)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    # --- Achievements ---
    def unlock_achievement(self, ach_id: str) -> bool:
        """Unlock an achievement if not already unlocked. Returns True if newly unlocked."""
        now_str = datetime.datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM achievements WHERE id = ?", (ach_id,))
            if cursor.fetchone():
                return False
            cursor.execute("INSERT INTO achievements (id, unlocked_at) VALUES (?, ?)", (ach_id, now_str))
            conn.commit()
            return True

    def get_unlocked_achievements(self) -> List[str]:
        """Get list of unlocked achievement IDs."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM achievements")
            rows = cursor.fetchall()
            return [r["id"] for r in rows]

    # --- Daily Fortune ---
    def get_daily_fortune(self, date_str: str) -> Optional[str]:
        """Fetch today's fortune message if already drawn."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT message FROM daily_fortunes WHERE date = ?", (date_str,))
            row = cursor.fetchone()
            return row["message"] if row else None

    def save_daily_fortune(self, date_str: str, message: str):
        """Save today's fortune message."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO daily_fortunes (date, message)
                VALUES (?, ?)
            """, (date_str, message))
            conn.commit()

    # --- Mood / Mental Wellness Trends ---
    def add_mood_entry(self, mood_type: str, score: int, snippet: str = ""):
        """Record sentiment analysis result from user conversation."""
        now = datetime.datetime.now()
        now_str = now.isoformat()
        date_str = now.strftime("%m/%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mood_history (timestamp, date, mood_type, score, snippet)
                VALUES (?, ?, ?, ?, ?)
            """, (now_str, date_str, mood_type, score, snippet[:100]))
            conn.commit()

    def get_recent_mood_history(self, limit: int = 14) -> List[Dict[str, Any]]:
        """Fetch chronological mood records for trend charts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, date, mood_type, score, snippet
                FROM mood_history
                ORDER BY id DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in reversed(rows)]

    # --- Lifetime Action Counters ---
    def increment_stat(self, key: str, amount: int = 1) -> int:
        """Increment a persistent lifetime stat counter."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO lifetime_stats (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = value + ?
            """, (key, amount, amount))
            conn.commit()
            cursor.execute("SELECT value FROM lifetime_stats WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else amount

    def get_stat(self, key: str, default: int = 0) -> int:
        """Get a persistent lifetime stat value."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM lifetime_stats WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def get_all_stats(self) -> Dict[str, int]:
        """Get all lifetime stats as a dictionary."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM lifetime_stats")
            rows = cursor.fetchall()
            return {r["key"]: r["value"] for r in rows}



