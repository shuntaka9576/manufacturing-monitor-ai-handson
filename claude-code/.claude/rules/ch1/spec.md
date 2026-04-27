---
paths:
  - "ch1/**/*"
---

# ch1: プロジェクト基盤 & DB - 実装仕様

## プロジェクト構成

```
ch1/
├── pyproject.toml       # 依存: streamlit, pandas, plotly, openpyxl
├── sample_data.xlsx     # マスタデータ（Excel）
├── db/
│   ├── __init__.py
│   ├── schema.sql       # DDL
│   ├── seed.py          # Excel読み込み → DB投入
│   └── connection.py    # DB接続ヘルパー
└── data/                # factory.db の格納先（gitignore対象）
```

## データベーススキーマ

### equipment テーブル（設備マスタ）

| カラム         | 型      | 制約                      | 説明                              |
| -------------- | ------- | ------------------------- | --------------------------------- |
| id             | INTEGER | PRIMARY KEY AUTOINCREMENT | 設備ID                            |
| name           | TEXT    | NOT NULL                  | 設備名（例: CNC旋盤 A-01）        |
| equipment_type | TEXT    | NOT NULL                  | 種類                              |
| location       | TEXT    | NOT NULL                  | 設置場所（例: A棟1F）             |
| installed_date | TEXT    | NOT NULL                  | 設置日（ISO 8601）                |
| status         | TEXT    | NOT NULL DEFAULT '稼働中' | ステータス（status_logsから導出） |

設備タイプは以下の4種類とする。

- CNC旋盤
- プレス機
- 射出成形機
- 溶接ロボット

ステータスは以下の4種類とする。

- 稼働中
- 停止中
- メンテナンス中
- 異常

### sensor_readings テーブル（センサー時系列データ）

| カラム       | 型      | 制約                         | 説明                 |
| ------------ | ------- | ---------------------------- | -------------------- |
| id           | INTEGER | PRIMARY KEY AUTOINCREMENT    | レコードID           |
| equipment_id | INTEGER | NOT NULL, FK → equipment(id) | 設備ID               |
| timestamp    | TEXT    | NOT NULL                     | 計測日時（ISO 8601） |
| temperature  | REAL    |                              | 温度（℃）            |
| vibration    | REAL    |                              | 振動（mm/s）         |
| rpm          | REAL    |                              | 回転数（RPM）        |
| power_kw     | REAL    |                              | 消費電力（kW）       |
| pressure     | REAL    |                              | 圧力（MPa）          |

インデックス: `(equipment_id, timestamp)` の複合インデックスを作成する。

### status_logs テーブル（ステータス変更履歴）

| カラム       | 型      | 制約                         | 説明                 |
| ------------ | ------- | ---------------------------- | -------------------- |
| id           | INTEGER | PRIMARY KEY AUTOINCREMENT    | レコードID           |
| equipment_id | INTEGER | NOT NULL, FK → equipment(id) | 設備ID               |
| timestamp    | TEXT    | NOT NULL                     | 変更日時（ISO 8601） |
| old_status   | TEXT    | NOT NULL                     | 変更前ステータス     |
| new_status   | TEXT    | NOT NULL                     | 変更後ステータス     |
| reason       | TEXT    |                              | 変更理由             |

インデックス: `(equipment_id, timestamp)` の複合インデックスを作成する。

## Excel構成（sample_data.xlsx）

3シート構成。全データがExcelに格納されており、seed.pyは読み込んでDBに投入するだけ。

### シート「設備マスタ」（8行）

| 列          | 内容                                     | 型   |
| ----------- | ---------------------------------------- | ---- |
| A: 設備名   | CNC旋盤 A-01 等                          | TEXT |
| B: タイプ   | CNC旋盤/プレス機/射出成形機/溶接ロボット | TEXT |
| C: 設置場所 | A棟1F 等                                 | TEXT |
| D: 設置日   | 2020-04-15 等                            | TEXT |

### シート「ステータス変更履歴」（59行）

| 列                  | 内容                              | 型      |
| ------------------- | --------------------------------- | ------- |
| A: 設備ID           | 1〜8                              | INTEGER |
| B: 設備名           | 表示用                            | TEXT    |
| C: 発生日時         | ISO 8601タイムスタンプ            | TEXT    |
| D: 変更前ステータス | 稼働中/停止中/メンテナンス中/異常 | TEXT    |
| E: 変更後ステータス | 同上                              | TEXT    |
| F: 理由             | 変更理由テキスト                  | TEXT    |

### シート「センサーデータ」（1,152行）

| 列                | 内容           | 型      |
| ----------------- | -------------- | ------- |
| A: 設備ID         | 1〜8           | INTEGER |
| B: タイムスタンプ | ISO 8601       | TEXT    |
| C: temperature    | 温度（℃）      | REAL    |
| D: vibration      | 振動（mm/s）   | REAL    |
| E: rpm            | 回転数（RPM）  | REAL    |
| F: power_kw       | 消費電力（kW） | REAL    |
| G: pressure       | 圧力（MPa）    | REAL    |

8設備 × 144ポイント（10分間隔 × 24時間）= 1,152行。
設備タイプごとに該当しないパラメータは None。

## シードデータ要件（seed.py）

seed.py は `sample_data.xlsx` を openpyxl で読み込み、DBにデータを投入する。ハードコードされたデータ定数は一切持たず、データの生成・変換も行わない。

### 処理フロー

1. `load_equipment_data(wb)` → 設備マスタシートから4列を読み込み
2. `load_status_log_events(wb)` → ステータス変更履歴シートからタイムスタンプを直接読み込み
3. `load_sensor_data(wb)` → センサーデータシートから時系列データを直接読み込み
4. `seed_equipment()` → equipment テーブルに INSERT（ステータスはDEFAULT '稼働中'）
5. `seed_status_logs()` → status_logs テーブルに INSERT
6. `seed_sensor_readings()` → sensor_readings テーブルに INSERT
7. `update_equipment_status()` → status_logs の最新エントリから各設備のステータスを UPDATE

## DB接続ヘルパー（connection.py）

- `get_connection()`: `row_factory = sqlite3.Row` を設定
- `query_df(sql, params)`: `pandas.DataFrame` で返す
- `STATUS_COLORS`: 稼働中=緑, 停止中=灰, メンテナンス中=黄, 異常=赤
- `THRESHOLDS`: 各センサーパラメータの警告・危険閾値
- `PARAM_LABELS`: パラメータの日本語ラベル

## 検証

```bash
uv sync && uv run python db/seed.py
# equipment: 8件, sensor_readings: 1,152件, status_logs: 59件
```
