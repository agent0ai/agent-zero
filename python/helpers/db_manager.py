"""
Database Manager for Agent Jumbo
Centralized SQLite connection handling and utilities
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any


class DatabaseManager:
    """Manages SQLite database connections and operations"""

    DEFAULT_DATA_DIR = "/a0/data"

    def __init__(self, db_name: str, data_dir: str | None = None):
        """
        Initialize database manager

        Args:
            db_name: Name of the database file (e.g., 'portfolio.db')
            data_dir: Directory for database files (default: /a0/data)
        """
        self.data_dir = Path(data_dir or self.DEFAULT_DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / db_name
        self._connection: sqlite3.Connection | None = None

    @property
    def connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    @contextmanager
    def cursor(self):
        """Context manager for database cursor"""
        cur = self.connection.cursor()
        try:
            yield cur
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cur.close()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL and return cursor"""
        with self.cursor() as cur:
            cur.execute(sql, params)
            return cur

    def execute_many(self, sql: str, params_list: list[tuple]) -> None:
        """Execute SQL for multiple parameter sets"""
        with self.cursor() as cur:
            cur.executemany(sql, params_list)

    def fetch_one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        """Fetch single row as dictionary"""
        with self.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def fetch_all(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Fetch all rows as list of dictionaries"""
        with self.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    def insert(self, table: str, data: dict[str, Any]) -> int:
        """Insert row and return last row id"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        with self.cursor() as cur:
            cur.execute(sql, tuple(data.values()))
            return cur.lastrowid

    def update(self, table: str, data: dict[str, Any], where: str, where_params: tuple) -> int:
        """Update rows and return affected count"""
        set_clause = ", ".join([f"{k} = ?" for k in data])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        with self.cursor() as cur:
            cur.execute(sql, tuple(data.values()) + where_params)
            return cur.rowcount

    def delete(self, table: str, where: str, where_params: tuple) -> int:
        """Delete rows and return affected count"""
        sql = f"DELETE FROM {table} WHERE {where}"
        with self.cursor() as cur:
            cur.execute(sql, where_params)
            return cur.rowcount

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        result = self.fetch_one("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return result is not None

    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Utility functions
def get_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"
