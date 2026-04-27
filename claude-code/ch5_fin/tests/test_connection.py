"""db/connection.py のテスト"""

import sqlite3

from db.connection import DB_PATH, get_connection, query_df


def test_db_file_exists():
    """データベースファイルが存在すること"""
    assert DB_PATH.exists(), f"DB file not found at {DB_PATH}. Run seed.py first."


def test_get_connection_returns_connection():
    """get_connection() がSQLiteコネクションを返すこと"""
    conn = get_connection()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_get_connection_row_factory():
    """get_connection() のrow_factoryがsqlite3.Rowに設定されていること"""
    conn = get_connection()
    assert conn.row_factory == sqlite3.Row
    conn.close()


def test_query_df_returns_dataframe():
    """query_df() がDataFrameを返すこと"""
    df = query_df("SELECT 1 AS test_col")
    assert len(df) == 1
    assert "test_col" in df.columns


def test_query_df_with_params():
    """query_df() がパラメータ付きクエリを処理できること"""
    df = query_df("SELECT * FROM equipment WHERE id = ?", (1,))
    assert len(df) == 1
    assert df.iloc[0]["name"] == "CNC旋盤 A-01"
