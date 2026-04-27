-- DBスキーマ定義: factory-dashboard-seed
-- 設備マスタ・ステータス変更履歴・センサーデータの3テーブルを定義する

-- 設備マスタテーブル
CREATE TABLE IF NOT EXISTS equipment (
    id            INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    type          TEXT    NOT NULL,
    location      TEXT    NOT NULL,
    installed_date TEXT   NOT NULL
);

-- ステータス変更履歴テーブル
CREATE TABLE IF NOT EXISTS status_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id    INTEGER NOT NULL REFERENCES equipment(id),
    equipment_name  TEXT    NOT NULL,
    occurred_at     TEXT    NOT NULL,
    status_before   TEXT    NOT NULL,
    status_after    TEXT    NOT NULL,
    reason          TEXT    NOT NULL
);

-- センサーデータテーブル
CREATE TABLE IF NOT EXISTS sensor_data (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    timestamp    TEXT    NOT NULL,
    temperature  REAL    NOT NULL,
    vibration    REAL    NOT NULL,
    rpm          REAL,
    power_kw     REAL    NOT NULL,
    pressure     REAL
);

-- インデックス定義
CREATE INDEX IF NOT EXISTS idx_status_history_equipment_id
    ON status_history (equipment_id);

CREATE INDEX IF NOT EXISTS idx_sensor_data_equipment_id
    ON sensor_data (equipment_id);

CREATE INDEX IF NOT EXISTS idx_sensor_data_equipment_timestamp
    ON sensor_data (equipment_id, timestamp);
