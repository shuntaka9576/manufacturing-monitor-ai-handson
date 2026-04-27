CREATE TABLE IF NOT EXISTS equipment (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    equipment_type TEXT    NOT NULL,
    location       TEXT    NOT NULL,
    installed_date TEXT    NOT NULL,
    status         TEXT    NOT NULL DEFAULT '稼働中'
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id  INTEGER NOT NULL REFERENCES equipment(id),
    timestamp     TEXT    NOT NULL,
    temperature   REAL,
    vibration     REAL,
    rpm           REAL,
    power_kw      REAL,
    pressure      REAL
);

CREATE TABLE IF NOT EXISTS status_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id  INTEGER NOT NULL REFERENCES equipment(id),
    timestamp     TEXT    NOT NULL,
    old_status    TEXT    NOT NULL,
    new_status    TEXT    NOT NULL,
    reason        TEXT
);

CREATE TABLE IF NOT EXISTS status_log_embeddings (
    status_log_id INTEGER PRIMARY KEY REFERENCES status_logs(id),
    embedding     BLOB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sensor_equip_time ON sensor_readings(equipment_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_status_equip_time ON status_logs(equipment_id, timestamp);
