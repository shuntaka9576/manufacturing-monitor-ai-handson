-- 設備マスタ
CREATE TABLE IF NOT EXISTS equipment (
    id                INTEGER PRIMARY KEY,
    name              TEXT NOT NULL,
    type              TEXT NOT NULL,
    location          TEXT NOT NULL,
    installation_date TEXT NOT NULL
);

-- ステータス変更履歴
CREATE TABLE IF NOT EXISTS status_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id    INTEGER NOT NULL,
    equipment_name  TEXT NOT NULL,
    occurred_at     TEXT NOT NULL,
    status_before   TEXT NOT NULL,
    status_after    TEXT NOT NULL,
    reason          TEXT NOT NULL,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

-- センサーデータ
CREATE TABLE IF NOT EXISTS sensor_data (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id  INTEGER NOT NULL,
    timestamp     TEXT NOT NULL,
    temperature   REAL,
    vibration     REAL,
    rpm           REAL,
    power_kw      REAL,
    pressure      REAL,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_status_history_equip_time
    ON status_history(equipment_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_sensor_data_equip_time
    ON sensor_data(equipment_id, timestamp);
