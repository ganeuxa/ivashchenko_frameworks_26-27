import sqlite3
from collections.abc import Sequence
from contextlib import closing
from datetime import datetime
from pathlib import Path

from db.database import BASE_DIR, get_connection
from models.stock import stock_gauge
from utils import DATE_FORMAT

QUERIES_FILE = BASE_DIR / "sql" / "queries.sql"
NAME_MARK = "-- name:"


def load_queries(path: Path = QUERIES_FILE) -> dict[str, str]:
    """Читает запросы из queries.sql по меткам «-- name: ...»."""
    queries: dict[str, str] = {}
    name = None
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(NAME_MARK):
            if name:
                queries[name] = "\n".join(lines).strip()
            name = line.removeprefix(NAME_MARK).strip()
            lines = []
        elif name and not line.lstrip().startswith("--"):
            lines.append(line)
    if name:
        queries[name] = "\n".join(lines).strip()
    return queries


QUERIES = load_queries()


def fetch_all(name: str, params: Sequence = ()) -> list[sqlite3.Row]:
    """Выполняет запрос по имени и возвращает все строки."""
    with closing(get_connection()) as conn:
        return conn.execute(QUERIES[name], params).fetchall()


def fetch_one(name: str, params: Sequence = ()) -> sqlite3.Row | None:
    """Выполняет запрос по имени и возвращает одну строку или None."""
    with closing(get_connection()) as conn:
        return conn.execute(QUERIES[name], params).fetchone()


def with_gauge(rows: list[sqlite3.Row]) -> list[dict]:
    """Добавляет к строкам с total и min_balance уровень и шкалу остатка."""
    return [
        {**dict(row), **stock_gauge(row["total"], row["min_balance"])}
        for row in rows
    ]


def with_dates(rows: list[sqlite3.Row]) -> list[dict]:
    """Превращает строку performed_at в datetime для фильтра date."""
    return [
        {
            **dict(row),
            "performed_at": datetime.strptime(
                row["performed_at"], DATE_FORMAT
            ),
        }
        for row in rows
    ]
