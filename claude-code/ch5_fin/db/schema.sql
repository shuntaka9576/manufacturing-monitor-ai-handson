PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS equipment(
    equipment_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    location TEXT NOT NULL,
    installed_on TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT '稼働中'
);

CREATE TABLE IF NOT EXISTS sensor_readings(
    equipment_id INTEGER NOT NULL REFERENCES equipment(equipment_id),
    timestamp TEXT NOT NULL,
    temperature REAL NOT NULL,
    vibration REAL NOT NULL,
    rpm REAL,
    power_kw REAL NOT NULL,
    pressure REAL,
    PRIMARY KEY (equipment_id, timestamp)
);

CREATE TABLE IF NOT EXISTS status_logs(
    equipment_id INTEGER NOT NULL REFERENCES equipment(equipment_id),
    occurred_at TEXT NOT NULL,
    prev_status TEXT NOT NULL,
    new_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    PRIMARY KEY (equipment_id, occurred_at)
);

CREATE TABLE IF NOT EXISTS status_log_embeddings(
    equipment_id INTEGER NOT NULL,
    occurred_at TEXT NOT NULL,
    embedding BLOB NOT NULL,
    PRIMARY KEY (equipment_id, occurred_at),
    FOREIGN KEY (equipment_id, occurred_at) REFERENCES status_logs(equipment_id, occurred_at)
);
