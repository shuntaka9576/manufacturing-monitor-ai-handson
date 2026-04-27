# 実装計画: factory-dashboard-seed

## 概要

Excelファイル（sample_data.xlsx）からSQLiteデータベースへのシードスクリプトを段階的に実装する。まずDBスキーマを定義し、次にseed.pyのコア機能を実装、最後にエラーハンドリングとテストを統合する。

## タスク

- [x] 1. DBスキーマファイルの作成
  - [x] 1.1 `db/schema.sql` を作成し、equipment / status_history / sensor_data の3テーブルのCREATE TABLE IF NOT EXISTS文を定義する
    - equipmentテーブル: id (INTEGER PRIMARY KEY), name (TEXT NOT NULL), type (TEXT NOT NULL), location (TEXT NOT NULL), installed_date (TEXT NOT NULL)
    - status_historyテーブル: id (INTEGER PRIMARY KEY AUTOINCREMENT), equipment_id (INTEGER NOT NULL REFERENCES equipment(id)), equipment_name (TEXT NOT NULL), occurred_at (TEXT NOT NULL), status_before (TEXT NOT NULL), status_after (TEXT NOT NULL), reason (TEXT NOT NULL)
    - sensor_dataテーブル: id (INTEGER PRIMARY KEY AUTOINCREMENT), equipment_id (INTEGER NOT NULL REFERENCES equipment(id)), timestamp (TEXT NOT NULL), temperature (REAL NOT NULL), vibration (REAL NOT NULL), rpm (REAL), power_kw (REAL NOT NULL), pressure (REAL)
    - status_historyにidx_status_history_equipment_idインデックスを作成
    - sensor_dataにidx_sensor_data_equipment_idインデックスとidx_sensor_data_equipment_timestamp複合インデックスを作成
    - _Requirements: 1.4, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4_

  - [x] 1.2 スキーマのユニットテストを作成する（`tests/test_seed.py`）
    - test_schema_has_all_tables: schema.sqlに3つのCREATE TABLE文が含まれること
    - test_schema_if_not_exists: IF NOT EXISTS句が含まれること
    - test_equipment_not_null_constraints: equipmentテーブルの全カラムにNOT NULL制約があること
    - test_foreign_key_status_history: status_historyのequipment_idに外部キー制約があること
    - test_foreign_key_sensor_data: sensor_dataのequipment_idに外部キー制約があること
    - test_indexes_exist: 必要なインデックスが全て作成されていること
    - _Requirements: 1.4, 2.1, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.4_

- [x] 2. seed.py のコア実装（Excel読み込み & データ投入）
  - [x] 2.1 `seed.py` を作成し、`load_excel(path)` 関数を実装する
    - pandasとopenpyxlエンジンを使用して設備マスタ・ステータス変更履歴・センサーデータの3シートを読み込む
    - シート名（設備マスタ, ステータス変更履歴, センサーデータ）で各シートを識別する
    - dict[str, pd.DataFrame] を返す
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 2.2 `validate_columns(sheets)` 関数を実装する
    - 各シートの必須カラムの存在を検証する
    - 不足カラムがある場合は不足カラム名を含む例外を送出する
    - _Requirements: 8.3_

  - [x] 2.3 `init_db(db_path, schema_path)` 関数を実装する
    - data/ ディレクトリが存在しない場合は作成する
    - SQLite接続を作成し、PRAGMA foreign_keys = ON を実行する
    - db/schema.sql を読み込んでexecutescriptでスキーマを実行する
    - _Requirements: 6.1, 6.2, 6.6_

  - [x] 2.4 `clear_tables(conn)` 関数を実装する
    - 外部キー制約を考慮した順序（sensor_data → status_history → equipment）で全テーブルのデータを削除する
    - _Requirements: 6.5_

  - [x] 2.5 `seed_equipment(conn, df)` / `seed_status_history(conn, df)` / `seed_sensor_data(conn, df)` 関数を実装する
    - 設備マスタ: 行番号（1から開始）をidとして割り当て、カラム名を日本語からDBカラム名にマッピングして投入
    - ステータス変更履歴: 6列をマッピングして投入
    - センサーデータ: 7列をマッピングし、rpm/pressureのNaN値をNoneに変換して投入
    - _Requirements: 5.2, 5.3, 5.4, 6.3_

  - [x] 2.6 `verify_counts(conn)` 関数を実装する
    - 各テーブルのレコード数を標準出力に表示する
    - 期待値（equipment: 8, status_history: 59, sensor_data: 1152）と比較し、不一致時は警告メッセージを表示する
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 2.7 `main()` 関数を実装し、全体の処理フローを統合する
    - Excelファイル存在確認 → Excel読み込み → カラム検証 → DB初期化 → データクリア → データ投入（トランザクション内） → コミット → レコード数検証
    - トランザクション管理: 全データ投入をアトミックに実行する
    - エラー時はトランザクションをロールバックし、sys.exit(1) で終了する
    - `if __name__ == "__main__": main()` でエントリポイントを定義する
    - _Requirements: 1.1, 1.2, 1.3, 6.4, 8.1, 8.2_

- [x] 3. チェックポイント - seed.py の動作確認
  - seed.py を実行し、data/factory.db が正しく作成されることを確認する
  - 各テーブルのレコード数が期待値と一致することを確認する
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. テストの実装
  - [x]* 4.1 `tests/test_seed.py` にseed.pyのユニットテストを追加する
    - test_seed_creates_db_file: seed.py実行後にdata/factory.dbが作成されること
    - test_foreign_keys_enabled: SQLite接続で外部キー制約が有効化されていること
    - test_record_counts: 各テーブルのレコード数が期待値と一致すること
    - test_error_missing_excel: Excelファイル不在時にエラーメッセージと非ゼロ終了コード
    - test_error_db_failure: DBエラー時にロールバックとエラーメッセージ
    - test_error_missing_columns: カラム不足時にエラーメッセージ
    - test_warning_count_mismatch: レコード数不一致時に警告メッセージ
    - _Requirements: 6.1, 6.6, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3_

  - [x]* 4.2 プロパティベーステスト: 設備IDの整合性（`tests/test_seed_props.py`）
    - **Property 1: 設備IDの整合性**
    - seed実行後のDBに対して、status_historyとsensor_dataの全equipment_idがequipmentテーブルのidに存在することを検証する
    - **Validates: Requirements 2.2, 6.3**

  - [x]* 4.3 プロパティベーステスト: センサーデータのNULL許容性と設備タイプの整合性（`tests/test_seed_props.py`）
    - **Property 2: センサーデータのNULL許容性と設備タイプの整合性**
    - sensor_dataレコードの対応するequipmentのtypeに基づいて、rpmとpressureのNULL/非NULLが正しいことを検証する
    - **Validates: Requirements 4.3**

  - [x]* 4.4 プロパティベーステスト: シード実行の冪等性（`tests/test_seed_props.py`）
    - **Property 3: シード実行の冪等性**
    - seed.pyを2回連続実行し、全テーブルの内容が同一であることを検証する
    - **Validates: Requirements 6.5**

- [x] 5. 最終チェックポイント - 全テスト実行
  - Ensure all tests pass, ask the user if questions arise.

## 備考

- `*` マーク付きのタスクはオプションであり、MVP実装時にはスキップ可能
- 各タスクは対応する要件番号を参照し、トレーサビリティを確保
- チェックポイントで段階的に動作を検証する
- プロパティベーステストは設計ドキュメントの正当性プロパティに対応
