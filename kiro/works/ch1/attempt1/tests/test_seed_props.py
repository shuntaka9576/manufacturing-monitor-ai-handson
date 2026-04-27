"""
tests/test_seed_props.py - seed.py のプロパティベーステスト
Feature: factory-dashboard-seed
"""

import sqlite3
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent))

import seed

SCHEMA_PATH = Path("db/schema.sql")
EXCEL_PATH = Path("sample_data.xlsx")


def _build_seeded_conn(db_path: Path) -> sqlite3.Connection:
    """テスト用にシード済み DB 接続を作成して返す"""
    conn = seed.init_db(db_path, SCHEMA_PATH)
    sheets = seed.load_excel(EXCEL_PATH)
    conn.execute("BEGIN")
    seed.clear_tables(conn)
    seed.seed_equipment(conn, sheets[seed.SHEET_EQUIPMENT])
    seed.seed_status_history(conn, sheets[seed.SHEET_STATUS_HISTORY])
    seed.seed_sensor_data(conn, sheets[seed.SHEET_SENSOR_DATA])
    conn.execute("COMMIT")
    return conn


# ---------------------------------------------------------------------------
# Property 1: 設備IDの整合性
# Feature: factory-dashboard-seed, Property 1: 設備IDの整合性
# Validates: Requirements 2.2, 6.3
# ---------------------------------------------------------------------------


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.data())
def test_prop_equipment_id_integrity(tmp_path, data):
    """
    seed 実行後の DB において、status_history と sensor_data の全 equipment_id が
    equipment テーブルの id に存在すること。
    """
    db_path = tmp_path / "factory.db"
    conn = _build_seeded_conn(db_path)

    equipment_ids = {
        row[0] for row in conn.execute("SELECT id FROM equipment").fetchall()
    }

    # status_history の全 equipment_id が equipment に存在すること
    sh_ids = {
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT equipment_id FROM status_history"
        ).fetchall()
    }
    assert sh_ids.issubset(equipment_ids), (
        f"status_history に不正な equipment_id が存在: {sh_ids - equipment_ids}"
    )

    # sensor_data の全 equipment_id が equipment に存在すること
    sd_ids = {
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT equipment_id FROM sensor_data"
        ).fetchall()
    }
    assert sd_ids.issubset(equipment_ids), (
        f"sensor_data に不正な equipment_id が存在: {sd_ids - equipment_ids}"
    )

    # equipment の id が 1 から始まる連番であること
    sorted_ids = sorted(equipment_ids)
    assert sorted_ids == list(range(1, len(sorted_ids) + 1)), (
        f"equipment の id が連番でない: {sorted_ids}"
    )

    conn.close()


# ---------------------------------------------------------------------------
# Property 2: センサーデータのNULL許容性と設備タイプの整合性
# Feature: factory-dashboard-seed, Property 2: センサーデータのNULL許容性と設備タイプの整合性
# Validates: Requirements 4.3
# ---------------------------------------------------------------------------

# 設備タイプとセンサー有無の対応
# CNC旋盤: rpm センサーあり（稼働中は正値、停止中は 0.0）、pressure センサーなし（NULL）
# プレス機・射出成形機: pressure センサーあり（稼働中は正値、停止中は 0.0）、rpm センサーなし（NULL）
# 溶接ロボット: rpm・pressure ともにセンサーなし（NULL）
#
# 注意: 停止期間中（ID4プレス機、ID8溶接ロボット）は 0.0 が混在するが、
#       これは NULL ではなく 0 値として格納されている実データの仕様。
#       「センサーなし」= NULL、「センサーあり・停止中」= 0.0 を区別する。
RPM_TYPES = {"CNC旋盤"}
PRESSURE_TYPES = {"プレス機", "射出成形機"}


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.data())
def test_prop_sensor_null_type_consistency(tmp_path, data):
    """
    sensor_data の各レコードについて、対応する equipment の type に基づき
    rpm / pressure の NULL / 非NULL が正しいこと。
    センサーを持たない設備タイプのカラムは NULL であること。
    センサーを持つ設備タイプのカラムは NULL でないこと（停止中の 0.0 は許容）。
    """
    db_path = tmp_path / "factory.db"
    conn = _build_seeded_conn(db_path)

    rows = conn.execute(
        """
        SELECT sd.rpm, sd.pressure, e.type
        FROM sensor_data sd
        JOIN equipment e ON sd.equipment_id = e.id
        """
    ).fetchall()

    for rpm, pressure, eq_type in rows:
        if eq_type in RPM_TYPES:
            # CNC旋盤: rpm センサーあり → NULL でないこと
            assert rpm is not None, f"CNC旋盤の rpm が NULL: type={eq_type}"
            # pressure センサーなし → NULL であること
            assert pressure is None, f"CNC旋盤の pressure が非NULL: type={eq_type}"
        elif eq_type in PRESSURE_TYPES:
            # プレス機・射出成形機: pressure センサーあり → NULL でないこと
            assert pressure is not None, f"{eq_type} の pressure が NULL"
            # rpm センサーなし → NULL であること
            # ただし停止期間中は rpm=0.0 かつ pressure=0.0 が混在する実データ仕様のため、
            # rpm が非NULL の場合は停止中（rpm=0.0 かつ pressure=0.0）であることを確認する
            if rpm is not None:
                assert rpm == 0.0 and pressure == 0.0, (
                    f"{eq_type} の rpm が非NULL かつ停止中でない: rpm={rpm}, pressure={pressure}"
                )
        else:
            # 溶接ロボット: rpm・pressure ともにセンサーなし → 両方 NULL
            # ただし停止期間中は 0.0 が混在する実データ仕様のため、
            # 非NULL の場合は停止中（両方 0.0）であることを確認する
            if rpm is not None:
                assert rpm == 0.0, (
                    f"{eq_type} の rpm が非NULL かつ 0.0 でない: rpm={rpm}"
                )
            if pressure is not None:
                assert pressure == 0.0, (
                    f"{eq_type} の pressure が非NULL かつ 0.0 でない: pressure={pressure}"
                )

    conn.close()


# ---------------------------------------------------------------------------
# Property 3: シード実行の冪等性
# Feature: factory-dashboard-seed, Property 3: シード実行の冪等性
# Validates: Requirements 6.5
# ---------------------------------------------------------------------------


def _seed_once(conn: sqlite3.Connection, sheets: dict) -> None:
    """clear → seed を1回実行する"""
    conn.execute("BEGIN")
    seed.clear_tables(conn)
    seed.seed_equipment(conn, sheets[seed.SHEET_EQUIPMENT])
    seed.seed_status_history(conn, sheets[seed.SHEET_STATUS_HISTORY])
    seed.seed_sensor_data(conn, sheets[seed.SHEET_SENSOR_DATA])
    conn.execute("COMMIT")


def _snapshot(conn: sqlite3.Connection) -> dict:
    """全テーブルの内容を id を除いたソート済みタプルのセットとして返す。
    AUTOINCREMENT の id は2回目のシードで増加するため比較対象から除外する。
    """
    queries = {
        "equipment": "SELECT id, name, type, location, installed_date FROM equipment ORDER BY id",
        "status_history": "SELECT equipment_id, equipment_name, occurred_at, status_before, status_after, reason FROM status_history ORDER BY equipment_id, occurred_at",
        "sensor_data": "SELECT equipment_id, timestamp, temperature, vibration, rpm, power_kw, pressure FROM sensor_data ORDER BY equipment_id, timestamp",
    }
    return {table: conn.execute(q).fetchall() for table, q in queries.items()}


@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.data())
def test_prop_seed_idempotency(tmp_path, data):
    """
    seed を2回連続実行した場合、全テーブルの内容が1回目と同一であること。
    """
    db_path = tmp_path / "factory.db"
    conn = seed.init_db(db_path, SCHEMA_PATH)
    sheets = seed.load_excel(EXCEL_PATH)

    _seed_once(conn, sheets)
    snapshot_1 = _snapshot(conn)

    _seed_once(conn, sheets)
    snapshot_2 = _snapshot(conn)

    assert snapshot_1 == snapshot_2, "2回目のシード後にデータが変化した（冪等性違反）"

    conn.close()
