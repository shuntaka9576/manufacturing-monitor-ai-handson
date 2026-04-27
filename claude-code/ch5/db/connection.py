"""SQLiteデータベース接続・クエリヘルパー"""

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent.parent / "data" / "factory.db"

THRESHOLDS = {
    "CNC旋盤": {
        "temperature": {"warning": 50, "critical": 60},
        "vibration": {"warning": 3.5, "critical": 4.5},
        "rpm": {"warning": 2400, "critical": 2800},
        "power_kw": {"warning": 13, "critical": 16},
    },
    "プレス機": {
        "temperature": {"warning": 60, "critical": 80},
        "vibration": {"warning": 7.0, "critical": 9.0},
        "power_kw": {"warning": 55, "critical": 70},
        "pressure": {"warning": 30, "critical": 40},
    },
    "射出成形機": {
        "temperature": {"warning": 240, "critical": 270},
        "vibration": {"warning": 2.5, "critical": 3.5},
        "power_kw": {"warning": 32, "critical": 38},
        "pressure": {"warning": 130, "critical": 160},
    },
    "溶接ロボット": {
        "temperature": {"warning": 75, "critical": 90},
        "vibration": {"warning": 4.5, "critical": 6.0},
        "power_kw": {"warning": 26, "critical": 32},
    },
}

PARAM_LABELS = {
    "temperature": "温度 (℃)",
    "vibration": "振動 (mm/s)",
    "rpm": "回転数 (RPM)",
    "power_kw": "電力 (kW)",
    "pressure": "圧力 (MPa)",
}


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df
