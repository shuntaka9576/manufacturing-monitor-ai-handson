"""Streamlitページの基本テスト"""

from db.connection import query_df


def test_history_query():
    """ステータス変更履歴クエリが正しくデータを返すこと"""
    df = query_df("""
        SELECT
            sl.timestamp AS 日時,
            e.name AS 設備名,
            sl.old_status AS 変更前,
            sl.new_status AS 変更後,
            sl.reason AS 理由
        FROM status_logs sl
        JOIN equipment e ON sl.equipment_id = e.id
        ORDER BY sl.timestamp DESC
    """)
    assert len(df) > 0
    assert "設備名" in df.columns
    assert "理由" in df.columns


def test_history_filter_by_equipment():
    """設備で絞り込んだ履歴クエリが正しく動作すること"""
    df = query_df(
        """
        SELECT
            sl.timestamp AS 日時,
            e.name AS 設備名,
            sl.old_status AS 変更前,
            sl.new_status AS 変更後,
            sl.reason AS 理由
        FROM status_logs sl
        JOIN equipment e ON sl.equipment_id = e.id
        WHERE sl.equipment_id = ?
        ORDER BY sl.timestamp DESC
    """,
        (1,),
    )
    assert len(df) > 0
    assert all(df["設備名"] == "CNC旋盤 A-01")


def test_equipment_data():
    """設備データが正しく取得できること"""
    df = query_df("SELECT id, name, equipment_type, location, status FROM equipment")
    assert len(df) == 8
    assert "status" in df.columns


def test_dashboard_sensor_query():
    """設備ダッシュボードのセンサーデータクエリが正しく動作すること"""
    df = query_df(
        "SELECT * FROM sensor_readings WHERE equipment_id = ? ORDER BY timestamp",
        (1,),
    )
    assert len(df) == 144
    assert "temperature" in df.columns
    assert "vibration" in df.columns


def test_dashboard_status_log_query():
    """設備ダッシュボードのステータス変更履歴クエリが正しく動作すること"""
    df = query_df(
        """
        SELECT
            timestamp AS 日時,
            old_status AS 変更前,
            new_status AS 変更後,
            reason AS 理由
        FROM status_logs
        WHERE equipment_id = ?
        ORDER BY timestamp DESC
    """,
        (1,),
    )
    assert len(df) > 0
    assert "理由" in df.columns
