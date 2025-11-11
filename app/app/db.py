"""
Simple database connection module using psycopg2.
This module provides a straightforward way to interact with PostgreSQL.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config
from contextlib import contextmanager


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Automatically handles connection opening and closing.

    Usage:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users")
                results = cur.fetchall()
    """
    conn = psycopg2.connect(Config.DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def execute_query(query, params=None, fetch=True):
    """
    Execute a SQL query and optionally fetch results.

    Args:
        query: SQL query string
        params: Tuple of parameters for the query
        fetch: Whether to fetch and return results (default: True)

    Returns:
        List of dictionaries if fetch=True, None otherwise
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            return None


def execute_query_one(query, params=None):
    """
    Execute a SQL query and fetch a single result.

    Args:
        query: SQL query string
        params: Tuple of parameters for the query

    Returns:
        Dictionary representing a single row, or None
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()

