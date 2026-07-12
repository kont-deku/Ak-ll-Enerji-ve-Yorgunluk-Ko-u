import sqlite3
from datetime import date

DB_PATH = "database/energy.db"


def get_connection(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Veritabanı şemasını başlatır ve gerekli tabloları oluşturur."""
    with get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                entry_date TEXT NOT NULL,
                sleep_hours REAL NOT NULL,
                water_amount REAL NOT NULL,
                phone_hours REAL NOT NULL,
                sport_status INTEGER NOT NULL,
                mood TEXT NOT NULL,
                energy_score INTEGER NOT NULL,
                energy_level TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)


def register_user(username, password, email, db_path: str = DB_PATH) -> bool:
    """Yeni kullanıcı kaydı oluşturur. Kullanıcı adı benzersiz olmalıdır."""
    try:
        with get_connection(db_path) as conn:
            conn.execute(
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                (username.strip(), password, email.strip())
            )
        return True
    except sqlite3.IntegrityError:
        return False


def login_user(username, password, db_path: str = DB_PATH):
    """Kimlik bilgilerini doğrular; eşleşme durumunda kullanıcı profilini döner."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT id, username, email FROM users WHERE username = ? AND password = ?",
            (username.strip(), password)
        ).fetchone()
        return dict(row) if row else None


def save_entry(user_id, sleep_hours, water_amount, phone_hours, sport_status, mood,
               energy_score, energy_level, entry_date: str = None,
               db_path: str = DB_PATH) -> int:
    """Günlük veriyi aktif kullanıcı ID'si ile ilişkilendirerek kaydeder."""
    entry_date = entry_date or date.today().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """INSERT INTO entries
               (user_id, entry_date, sleep_hours, water_amount, phone_hours, sport_status, mood,
                energy_score, energy_level)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, entry_date, sleep_hours, water_amount, phone_hours,
             int(bool(sport_status)), mood, energy_score, energy_level)
        )
        return cursor.lastrowid


def get_previous_entry(user_id, before_date: str = None, db_path: str = DB_PATH):
    """Belirtilen tarihten önce, ilgili kullanıcıya ait son kaydı getirir."""
    before_date = before_date or date.today().isoformat()
    with get_connection(db_path) as conn:
        row = conn.execute(
            """SELECT * FROM entries
               WHERE user_id = ? AND entry_date < ?
               ORDER BY entry_date DESC, id DESC LIMIT 1""",
            (user_id, before_date),
        ).fetchone()
        return dict(row) if row else None


def get_entry(entry_id, db_path: str = DB_PATH):
    """Tek bir kaydı ID'sine göre getirir."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
        return dict(row) if row else None


def get_history(user_id, limit: int = 30, db_path: str = DB_PATH):
    """Oturum sahibi kullanıcının geçmiş verilerini listeler."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM entries WHERE user_id = ? ORDER BY entry_date DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
