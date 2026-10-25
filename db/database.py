import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "consumables.sqlite"
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Открывает базу: проверка внешних ключей и доступ к полям по имени."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Создаёт таблицы из sql/schema.sql, если их ещё нет."""
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
