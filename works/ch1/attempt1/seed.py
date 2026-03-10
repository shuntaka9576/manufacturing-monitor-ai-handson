"""
seed.py - factory-dashboard-seed
Excelファイル（sample_data.xlsx）からSQLiteデータベース（data/factory.db）にデータを投入するシードスクリプト。
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

# ファイルパス定数
EXCEL_PATH = Path("sample_data.xlsx")
DB_PATH = Path("data/factory.db")
SCHEMA_PATH = Path("db/schema.sql")

# Excelシート名
SHEET_EQUIPMENT = "設備マスタ"
SHEET_STATUS_HISTORY = "ステータス変更履歴"
SHEET_SENSOR_DATA = "センサーデータ"

# 各シートの必須カラム
REQUIRED_COLUMNS = {
    SHEET_EQUIPMENT: ["設備名", "タイプ", "設置場所", "設置日"],
    SHEET_STATUS_HISTORY: [
        "設備ID",
        "設備名",
        "発生日時",
        "変更前ステータス",
        "変更後ステータス",
        "理由",
    ],
    SHEET_SENSOR_DATA: [
        "設備ID",
        "タイムスタンプ",
        "temperature",
        "vibration",
        "rpm",
        "power_kw",
        "pressure",
    ],
}

# レコード数の期待値
EXPECTED_COUNTS = {
    "equipment": 8,
    "status_history": 59,
    "sensor_data": 1152,
}


def load_excel(path: Path) -> dict[str, pd.DataFrame]:
    """Excelファイルの3シートを読み込み、DataFrameの辞書を返す。"""
    sheets = pd.read_excel(
        path,
        sheet_name=[SHEET_EQUIPMENT, SHEET_STATUS_HISTORY, SHEET_SENSOR_DATA],
        engine="openpyxl",
    )
    return sheets


def validate_columns(sheets: dict[str, pd.DataFrame]) -> None:
    """各シートの必須カラムの存在を検証する。不足カラムがある場合は例外を送出する。"""
    for sheet_name, required in REQUIRED_COLUMNS.items():
        df = sheets[sheet_name]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(
                f"[ERROR] シート「{sheet_name}」に必須カラムが不足しています: {missing}"
            )


def init_db(db_path: Path, schema_path: Path) -> sqlite3.Connection:
    """DBディレクトリを作成し、SQLite接続を初期化してスキーマを実行する。"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_sql = schema_path.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    return conn


def clear_tables(conn: sqlite3.Connection) -> None:
    """外部キー制約を考慮した順序で全テーブルのデータを削除する。"""
    conn.execute("DELETE FROM sensor_data")
    conn.execute("DELETE FROM status_history")
    conn.execute("DELETE FROM equipment")


def seed_equipment(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    """設備マスタデータを投入する。行番号（1から開始）をidとして使用する。"""
    records = []
    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        records.append(
            (
                idx,
                row["設備名"],
                row["タイプ"],
                row["設置場所"],
                str(row["設置日"]),
            )
        )
    conn.executemany(
        "INSERT INTO equipment (id, name, type, location, installed_date) VALUES (?, ?, ?, ?, ?)",
        records,
    )


def seed_status_history(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    """ステータス変更履歴データを投入する。"""
    records = [
        (
            int(row["設備ID"]),
            row["設備名"],
            row["発生日時"],
            row["変更前ステータス"],
            row["変更後ステータス"],
            row["理由"],
        )
        for _, row in df.iterrows()
    ]
    conn.executemany(
        "INSERT INTO status_history (equipment_id, equipment_name, occurred_at, status_before, status_after, reason) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        records,
    )


def seed_sensor_data(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    """センサーデータを投入する。rpm/pressureのNaN値はNoneに変換する。"""
    records = []
    for _, row in df.iterrows():
        rpm = None if pd.isna(row["rpm"]) else float(row["rpm"])
        pressure = None if pd.isna(row["pressure"]) else float(row["pressure"])
        records.append(
            (
                int(row["設備ID"]),
                row["タイムスタンプ"],
                float(row["temperature"]),
                float(row["vibration"]),
                rpm,
                float(row["power_kw"]),
                pressure,
            )
        )
    conn.executemany(
        "INSERT INTO sensor_data (equipment_id, timestamp, temperature, vibration, rpm, power_kw, pressure) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        records,
    )


def verify_counts(conn: sqlite3.Connection) -> bool:
    """各テーブルのレコード数を検証・表示する。全て一致すればTrueを返す。"""
    all_ok = True
    for table, expected in EXPECTED_COUNTS.items():
        actual = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {actual} 件")
        if actual != expected:
            print(
                f"[WARNING] レコード数が期待値と一致しません: {table} (期待: {expected}, 実際: {actual})"
            )
            all_ok = False
    return all_ok


def main() -> None:
    """エントリポイント。全体の処理フローを制御する。"""
    # Excelファイル存在確認
    if not EXCEL_PATH.exists():
        print(f"[ERROR] sample_data.xlsx が見つかりません: {EXCEL_PATH.resolve()}")
        sys.exit(1)

    # スキーマファイル存在確認
    if not SCHEMA_PATH.exists():
        print(f"[ERROR] db/schema.sql が見つかりません: {SCHEMA_PATH.resolve()}")
        sys.exit(1)

    # Excel読み込み
    print("Excelファイルを読み込んでいます...")
    sheets = load_excel(EXCEL_PATH)

    # カラム検証
    try:
        validate_columns(sheets)
    except ValueError as e:
        print(str(e))
        sys.exit(1)

    # DB初期化
    print("データベースを初期化しています...")
    conn = init_db(DB_PATH, SCHEMA_PATH)

    # データ投入（トランザクション内）
    try:
        conn.execute("BEGIN")
        clear_tables(conn)
        print("設備マスタを投入しています...")
        seed_equipment(conn, sheets[SHEET_EQUIPMENT])
        print("ステータス変更履歴を投入しています...")
        seed_status_history(conn, sheets[SHEET_STATUS_HISTORY])
        print("センサーデータを投入しています...")
        seed_sensor_data(conn, sheets[SHEET_SENSOR_DATA])
        conn.execute("COMMIT")
        print("データ投入が完了しました。")
    except sqlite3.Error as e:
        conn.execute("ROLLBACK")
        print(f"[ERROR] データベースエラー: {e}")
        sys.exit(1)
    finally:
        conn.close()

    # レコード数検証
    conn = sqlite3.connect(DB_PATH)
    print("\nレコード数を確認しています...")
    verify_counts(conn)
    conn.close()


if __name__ == "__main__":
    main()
