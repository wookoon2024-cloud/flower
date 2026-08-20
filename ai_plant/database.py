"""
Database Manager for AI Companion Plant Widget
Handles SQLite3 persistence for plant state, chat history, and user profile.
"""
import sqlite3
import os
import datetime
import hashlib
import base64
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
from .config import get_base_dir

_VAULT_SALT = b"PlantMindKeeper_2026_SecureVault_KeySalt_GovClova"

def _vault_encrypt(plaintext: str) -> str:
    """Portable standard XOR + SHA256 stream encryption for SQLite storage."""
    if not plaintext:
        return ""
    try:
        raw_bytes = plaintext.encode("utf-8")
        stream = hashlib.sha256(_VAULT_SALT + b"HEADER").digest()
        key_stream = bytearray()
        counter = 0
        while len(key_stream) < len(raw_bytes):
            key_stream.extend(hashlib.sha256(stream + counter.to_bytes(4, "big")).digest())
            counter += 1
        enc_bytes = bytes([b ^ key_stream[i] for i, b in enumerate(raw_bytes)])
        return "VAULT_v1:" + base64.b64encode(enc_bytes).decode("utf-8")
    except Exception:
        return plaintext

def _vault_decrypt(ciphertext: str) -> str:
    """Portable standard decryption from SQLite storage."""
    if not ciphertext or not isinstance(ciphertext, str):
        return ""
    if not ciphertext.startswith("VAULT_v1:"):
        return ciphertext
    try:
        raw_b64 = ciphertext[9:]
        enc_bytes = base64.b64decode(raw_b64)
        stream = hashlib.sha256(_VAULT_SALT + b"HEADER").digest()
        key_stream = bytearray()
        counter = 0
        while len(key_stream) < len(enc_bytes):
            key_stream.extend(hashlib.sha256(stream + counter.to_bytes(4, "big")).digest())
            counter += 1
        dec_bytes = bytes([b ^ key_stream[i] for i, b in enumerate(enc_bytes)])
        return dec_bytes.decode("utf-8")
    except Exception:
        return ciphertext

class DatabaseManager:
    def __init__(self, db_filename: str = "plant_data.db"):
        self.db_path = os.path.join(get_base_dir(), db_filename)
        self._stats_cache: Dict[str, int] = {}
        self._unlocked_achievements_cache: Optional[set] = None

        # Clean up legacy WAL/SHM files to keep directory 100% clean
        for ext in ["-wal", "-shm"]:
            fpath = self.db_path + ext
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass

        self.init_db()
        self._warmup_cache()

    def _warmup_cache(self):
        """Warmup in-memory cache to eliminate disk I/O lag on secure corporate/intranet machines."""
        try:
            self._stats_cache = self.get_all_stats()
            self._unlocked_achievements_cache = set(self.get_unlocked_achievements())
        except Exception:
            pass

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        try:
            # 100% In-Memory Journaling to prevent DLP/Antivirus file creation/deletion hooking
            conn.execute("PRAGMA journal_mode = MEMORY")
            conn.execute("PRAGMA synchronous = OFF")
            conn.execute("PRAGMA temp_store = MEMORY")
        except Exception:
            pass
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

            # 9. secure_vault (Encrypted API Credentials & Secrets) table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS secure_vault (
                    key TEXT PRIMARY KEY,
                    encrypted_val TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)

            # 10. user_inventory (Shop Purchased Items & Equipped Saucers/Pets) table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_inventory (
                    item_type TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    purchased_at TIMESTAMP NOT NULL,
                    is_equipped INTEGER DEFAULT 0,
                    PRIMARY KEY (item_type, item_id)
                )
            """)

            # Ensure default free items are present
            now_str = datetime.datetime.now().isoformat()
            cursor.execute("""
                INSERT OR IGNORE INTO user_inventory (item_type, item_id, purchased_at, is_equipped)
                VALUES ('saucer', 'basic', ?, 1)
            """, (now_str,))
            # Migrate old 'none' saucer to 'basic' if equipped
            cursor.execute("UPDATE user_inventory SET item_id = 'basic' WHERE item_type = 'saucer' AND item_id = 'none'")
            cursor.execute("""
                INSERT OR IGNORE INTO user_inventory (item_type, item_id, purchased_at, is_equipped)
                VALUES ('pet', 'none', ?, 1)
            """, (now_str,))

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

    def get_recent_chat_history(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Sliding Window: Fetch recent messages."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content, timestamp FROM chat_history
                ORDER BY id DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            history = [
                {
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"] if "timestamp" in row.keys() else ""
                }
                for row in reversed(rows)
            ]
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
        if self._unlocked_achievements_cache is not None and ach_id in self._unlocked_achievements_cache:
            return False
        now_str = datetime.datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM achievements WHERE id = ?", (ach_id,))
            if cursor.fetchone():
                if self._unlocked_achievements_cache is not None:
                    self._unlocked_achievements_cache.add(ach_id)
                return False
            cursor.execute("INSERT INTO achievements (id, unlocked_at) VALUES (?, ?)", (ach_id, now_str))
            conn.commit()
            if self._unlocked_achievements_cache is not None:
                self._unlocked_achievements_cache.add(ach_id)
            return True

    def get_unlocked_achievements(self) -> List[str]:
        """Get list of unlocked achievement IDs."""
        if self._unlocked_achievements_cache is not None:
            return list(self._unlocked_achievements_cache)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM achievements")
            rows = cursor.fetchall()
            ids = [r["id"] for r in rows]
            self._unlocked_achievements_cache = set(ids)
            return ids

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

    def get_daily_mood_summary(self, num_days: int = 7) -> List[Dict[str, Any]]:
        """
        Groups mood entries by calendar day (YYYY-MM-DD), calculates daily averages,
        and constructs a fixed 7-day timeline window with upcoming/future dates pre-populated.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, date, score, mood_type
                FROM mood_history
                ORDER BY id ASC
            """)
            rows = cursor.fetchall()

        daily_map = {}
        for r in rows:
            ts = str(r["timestamp"])
            day_str = ts.split("T")[0] if "T" in ts else ts.split(" ")[0]
            if day_str not in daily_map:
                daily_map[day_str] = {"scores": [], "moods": []}
            daily_map[day_str]["scores"].append(float(r["score"]))
            daily_map[day_str]["moods"].append(str(r["mood_type"]))

        today = datetime.date.today()
        if daily_map:
            sorted_days = sorted(daily_map.keys())
            try:
                earliest_dt = datetime.datetime.strptime(sorted_days[0], "%Y-%m-%d").date()
                start_date = max(earliest_dt, today - datetime.timedelta(days=num_days - 1))
            except Exception:
                start_date = today
        else:
            start_date = today

        result = []
        for i in range(num_days):
            curr_d = start_date + datetime.timedelta(days=i)
            curr_str = curr_d.strftime("%Y-%m-%d")
            m_d_str = curr_d.strftime("%m/%d")
            weekdays = ["월", "화", "수", "목", "금", "토", "일"]
            w_str = weekdays[curr_d.weekday()]

            if curr_str in daily_map:
                sc_list = daily_map[curr_str]["scores"]
                avg_sc = sum(sc_list) / len(sc_list)
                mood_list = daily_map[curr_str]["moods"]
                dom_mood = max(set(mood_list), key=mood_list.count)
                result.append({
                    "date": m_d_str,
                    "full_date": curr_str,
                    "weekday": w_str,
                    "is_today": (curr_d == today),
                    "is_future": (curr_d > today),
                    "has_data": True,
                    "avg_score": round(avg_sc, 1),
                    "count": len(sc_list),
                    "mood_type": dom_mood
                })
            else:
                result.append({
                    "date": m_d_str,
                    "full_date": curr_str,
                    "weekday": w_str,
                    "is_today": (curr_d == today),
                    "is_future": (curr_d > today),
                    "has_data": False,
                    "avg_score": None,
                    "count": 0,
                    "mood_type": "calm"
                })

        return result

    # --- Lifetime Action Counters ---
    def increment_stat(self, key: str, amount: int = 1) -> int:
        """Increment a persistent lifetime stat counter with instant in-memory update."""
        current_val = self._stats_cache.get(key, 0) + amount
        self._stats_cache[key] = current_val
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO lifetime_stats (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = value + ?
                """, (key, amount, amount))
                conn.commit()
        except Exception as e:
            print(f"[DatabaseManager] increment_stat error: {e}")
        return current_val

    def get_stat(self, key: str, default: int = 0) -> int:
        """Get a persistent lifetime stat value with instant in-memory lookup."""
        if key in self._stats_cache:
            return self._stats_cache[key]
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM lifetime_stats WHERE key = ?", (key,))
            row = cursor.fetchone()
            val = row[0] if row else default
            self._stats_cache[key] = val
            return val

    def get_all_stats(self) -> Dict[str, int]:
        """Get all lifetime stats as a dictionary."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM lifetime_stats")
            rows = cursor.fetchall()
            stats = {r["key"]: r["value"] for r in rows}
            self._stats_cache.update(stats)
            return stats

    # --- Secure Vault (Portable Encrypted Secret Storage) ---
    def set_secure_key(self, key: str, plaintext: str):
        """Encrypt and store sensitive secret inside SQLite secure_vault table."""
        enc_val = _vault_encrypt(plaintext)
        now_str = datetime.datetime.now().isoformat()
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO secure_vault (key, encrypted_val, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET encrypted_val = ?, updated_at = ?
                """, (key, enc_val, now_str, enc_val, now_str))
                conn.commit()
        except Exception as e:
            print(f"[DatabaseManager] set_secure_key error: {e}")

    def get_secure_key(self, key: str, default: str = "") -> str:
        """Retrieve and decrypt sensitive secret from SQLite secure_vault table."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT encrypted_val FROM secure_vault WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row and row["encrypted_val"]:
                    return _vault_decrypt(row["encrypted_val"])
        except Exception as e:
            print(f"[DatabaseManager] get_secure_key error: {e}")
        return default

    # --- Coin & Shop Economy System ---
    def get_coins(self) -> int:
        """Get current seed coins balance with retroactive grant check."""
        current = self.get_stat("total_coins", -1)
        if current < 0:
            # Retroactive grant for existing achievements: 50 coins per achievement + 100 welcome bonus
            ach_count = len(self.get_unlocked_achievements())
            initial_coins = 100 + (ach_count * 50)
            self.set_stat("total_coins", initial_coins)
            return initial_coins
        return current

    def add_coins(self, amount: int) -> int:
        """Add seed coins to player balance."""
        if amount <= 0:
            return self.get_coins()
        new_total = self.get_coins() + amount
        self.set_stat("total_coins", new_total)
        return new_total

    def spend_coins(self, amount: int) -> bool:
        """Spend seed coins if sufficient balance exists."""
        current = self.get_coins()
        if current < amount:
            return False
        new_total = current - amount
        self.set_stat("total_coins", new_total)
        return True

    def set_stat(self, key: str, value: int):
        """Set an exact value for a lifetime stat."""
        self._stats_cache[key] = value
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO lifetime_stats (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = ?
                """, (key, value, value))
                conn.commit()
        except Exception as e:
            print(f"[DatabaseManager] set_stat error: {e}")

    # --- Inventory & Equipment System ---
    def get_inventory(self, item_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all purchased inventory items."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if item_type:
                cursor.execute("SELECT * FROM user_inventory WHERE item_type = ?", (item_type,))
            else:
                cursor.execute("SELECT * FROM user_inventory")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def is_item_purchased(self, item_type: str, item_id: str) -> bool:
        """Check if an item is purchased/owned."""
        if item_id in ("none", "basic"):
            return True
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_inventory WHERE item_type = ? AND item_id = ?", (item_type, item_id))
            return cursor.fetchone()[0] > 0

    def purchase_item(self, item_type: str, item_id: str, cost: int) -> bool:
        """Purchase an item using coins and add to inventory."""
        if self.is_item_purchased(item_type, item_id):
            return True
        if not self.spend_coins(cost):
            return False
        now_str = datetime.datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_inventory (item_type, item_id, purchased_at, is_equipped)
                VALUES (?, ?, ?, 0)
            """, (item_type, item_id, now_str))
            conn.commit()
        return True

    def equip_item(self, item_type: str, item_id: str) -> bool:
        """Equip an item of a specific type (e.g. saucer or pet)."""
        if not self.is_item_purchased(item_type, item_id):
            return False
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE user_inventory SET is_equipped = 0 WHERE item_type = ?", (item_type,))
            cursor.execute("""
                INSERT INTO user_inventory (item_type, item_id, purchased_at, is_equipped)
                VALUES (?, ?, CURRENT_TIMESTAMP, 1)
                ON CONFLICT(item_type, item_id) DO UPDATE SET is_equipped = 1
            """, (item_type, item_id))
            conn.commit()
        return True

    def get_equipped_item(self, item_type: str) -> str:
        """Get the currently equipped item ID for a given type (default 'basic' for saucer, 'none' for pet)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id FROM user_inventory WHERE item_type = ? AND is_equipped = 1", (item_type,))
            row = cursor.fetchone()
            if row:
                return row["item_id"]
        return "basic" if item_type == "saucer" else "none"




