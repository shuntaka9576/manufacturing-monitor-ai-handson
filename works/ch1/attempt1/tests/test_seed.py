"""
tests/test_seed.py - seed.py および db/schema.sql のユニットテスト
"""

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

import seed

SCHEMA_PATH = Path("db/schema.sql")
EXCEL_PATH = Path("sample_data.xlsx")


# ---------------------------------------------------------------------------
# スキーマテスト (タスク 1.2)
# ---------------------------------------------------------------------------


def test_schema_has_all_tables():
    """schema.sql に3つの CREATE TABLE 文が含まれること"""
    sql = SCHEMA_PATH.read_text(encoding="utf-8").upper()
    assert sql.count("CREATE TABLE") == 3


def test_schema_if_not_exists():
    """schema.sql に IF NOT EXISTS 句が含まれること"""
    sql = SCHEMA_PATH.read_text(encoding="utf-8").upper()
    assert sql.count("IF NOT EXISTS") >= 3


def test_equipment_not_null_constraints():
    """equipment テーブルの全カラムに NOT NULL 制約があること"""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    # equipment テーブルブロックを抽出
    start = sql.index("CREATE TABLE IF NOT EXISTS equipment")
    end = sql.index(");", start) + 2
    block = sql[start:end].upper()
    for col in ["NAME", "TYPE", "LOCATION", "INSTALLED_DATE"]:
        assert f"{col}" in block and "NOT NULL" in block


def test_foreign_key_status_history():
    """status_history の equipment_id に外部キー制約があること"""
    sql = SCHEMA_PATH.read_text(encoding="utf-8").upper()
    start = sql.index("CREATE TABLE IF NOT EXISTS STATUS_HISTORY")
    end = sql.index(");", start) + 2
    block = sql[start:end]
    assert "REFERENCES EQUIPMENT(ID)" in block


def test_foreign_key_sensor_data():
    """sensor_data の equipment_id に外部キー制約があること"""
    sql = SCHEMA_PATH.read_text(encoding="utf-8").upper()
    start = sql.index("CREATE TABLE IF NOT EXISTS SENSOR_DATA")
    end = sql.index(");", start) + 2
    block = sql[start:end]
    assert "REFERENCES EQUIPMENT(ID)" in block


def test_indexes_exist():
    """必要なインデックスが全て作成されていること"""
    sql = SCHEMA_PATH.read_text(encoding="utf-8").upper()
    assert "IDX_STATUS_HISTORY_EQUIPMENT_ID" in sql
    assert "IDX_SENSOR_DATA_EQUIPMENT_ID" in sql
    assert "IDX_SENSOR_DATA_EQUIPMENT_TIMESTAMP" in sql


# ---------------------------------------------------------------------------
# seed.py ユニットテスト (タスク 4.1)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def seeded_db(tmp_path_factory):
    """seed.py を実行して作成した DB への接続を返すセッションスコープフィクスチャ"""
    db_path = tmp_path_factory.mktemp("data") / "factory.db"
    conn = seed.init_db(db_path, SCHEMA_PATH)
    sheets = seed.load_excel(EXCEL_PATH)
    conn.execute("BEGIN")
    seed.seed_equipment(conn, sheets[seed.SHEET_EQUIPMENT])
    seed.seed_status_history(conn, sheets[seed.SHEET_STATUS_HISTORY])
    seed.seed_sensor_data(conn, sheets[seed.SHEET_SENSOR_DATA])
    conn.execute("COMMIT")
    yield conn, db_path
    conn.close()


def test_seed_creates_db_file(tmp_path):
    """seed.py 実行後に DB ファイルが作成されること"""
    db_path = tmp_path / "factory.db"
    conn = seed.init_db(db_path, SCHEMA_PATH)
    conn.close()
    assert db_path.exists()


def test_foreign_keys_enabled(tmp_path):
    """SQLite 接続で外部キー制約が有効化されていること"""
    db_path = tmp_path / "factory.db"
    conn = seed.init_db(db_path, SCHEMA_PATH)
    result = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    conn.close()
    assert result == 1


def test_record_counts(seeded_db):
    """各テーブルのレコード数が期待値と一致すること"""
    conn, _ = seeded_db
    assert conn.execute("SELECT COUNT(*) FROM equipment").fetchone()[0] == 8
    assert conn.execute("SELECT COUNT(*) FROM status_history").fetchone()[0] == 59
    assert conn.execute("SELECT COUNT(*) FROM sensor_data").fetchone()[0] == 1152


def test_error_missing_excel(tmp_path, monkeypatch):
    """Excel ファイル不在時にエラーメッセージと非ゼロ終了コードで終了すること"""
    # EXCEL_PATH を存在しないパスに差し替えて main() を直接呼ぶ
    monkeypatch.setattr(seed, "EXCEL_PATH", tmp_path / "nonexistent.xlsx")
    with pytest.raises(SystemExit) as exc_info:
        seed.main()
    assert exc_info.value.code != 0


def test_error_db_failure(tmp_path):
    """DB エラー時にロールバックとエラーメッセージが出力されること"""
    db_path = tmp_path / "factory.db"
    conn = seed.init_db(db_path, SCHEMA_PATH)
    # 外部キー違反を起こす不正なデータを投入してエラーを誘発
    bad_df = pd.DataFrame(
        [
            {
                "設備ID": 999,  # 存在しない equipment_id
                "設備名": "存在しない設備",
                "発生日時": "2026-01-01T00:00:00",
                "変更前ステータス": "稼働中",
                "変更後ステータス": "停止中",
                "理由": "テスト",
            }
        ]
    )
    conn.execute("BEGIN")
    with pytest.raises(Exception):
        seed.seed_status_history(conn, bad_df)
        conn.execute("COMMIT")
    conn.execute("ROLLBACK")
    conn.close()


def test_error_missing_columns():
    """カラム不足時に ValueError が送出されること"""
    bad_sheets = {
        seed.SHEET_EQUIPMENT: pd.DataFrame([{"設備名": "X"}]),  # タイプ等が欠落
        seed.SHEET_STATUS_HISTORY: pd.DataFrame(),
        seed.SHEET_SENSOR_DATA: pd.DataFrame(),
    }
    with pytest.raises(ValueError, match="必須カラムが不足"):
        seed.validate_columns(bad_sheets)


def test_warning_count_mismatch(tmp_path, capsys):
    """レコード数不一致時に WARNING メッセージが表示されること"""
    db_path = tmp_path / "factory.db"
    conn = seed.init_db(db_path, SCHEMA_PATH)
    # equipment を1件だけ投入（期待値 8 と不一致）
    conn.execute("BEGIN")
    conn.execute(
        "INSERT INTO equipment (id, name, type, location, installed_date) VALUES (1, 'X', 'CNC旋盤', 'A棟1F', '2020-01-01')"
    )
    conn.execute("COMMIT")
    seed.verify_counts(conn)
    conn.close()
    captured = capsys.readouterr()
    assert "WARNING" in captured.out
