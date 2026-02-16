# -*- coding: utf-8 -*-
"""
SQLite database for storing OSINT results
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules.config import DB_PATH
from modules.logger import log


def get_connection() -> sqlite3.Connection:
    """Get database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables"""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS phone_lookups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                country TEXT,
                carrier TEXT,
                accounts TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tweet_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tweet_id TEXT,
                username TEXT,
                url TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL,
                longitude REAL,
                accuracy REAL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_type TEXT,
                query TEXT,
                result_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    except Exception as e:
        log.error(f"Database init failed: {e}")
    finally:
        conn.close()


def save_phone_lookup(phone: str, country: str, carrier: str, accounts: Dict) -> None:
    """Save phone lookup result"""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO phone_lookups (phone_number, country, carrier, accounts) VALUES (?, ?, ?, ?)",
            (phone, country, carrier, json.dumps(accounts))
        )
        conn.commit()
    except Exception as e:
        log.error(f"Save phone lookup failed: {e}")
    finally:
        conn.close()


def save_tweet_analysis(tweet_id: str, username: str, url: str, data: Dict) -> None:
    """Save tweet analysis result"""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO tweet_analyses (tweet_id, username, url, data) VALUES (?, ?, ?, ?)",
            (tweet_id, username, url, json.dumps(data))
        )
        conn.commit()
    except Exception as e:
        log.error(f"Save tweet analysis failed: {e}")
    finally:
        conn.close()


def save_search(type_name: str, query: str, result_count: int) -> None:
    """Save search to history"""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO search_history (search_type, query, result_count) VALUES (?, ?, ?)",
            (type_name, query, result_count)
        )
        conn.commit()
    except Exception as e:
        log.error(f"Save search failed: {e}")
    finally:
        conn.close()
