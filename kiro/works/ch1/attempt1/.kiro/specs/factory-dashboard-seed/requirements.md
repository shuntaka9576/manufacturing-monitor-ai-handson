# 要件定義書

## はじめに

製造設備の稼働状況をリアルタイムで監視するダッシュボードアプリのデータ基盤を構築する。Excelファイル（sample_data.xlsx）に格納された設備マスタ・ステータス変更履歴・センサーデータを読み込み、SQLiteデータベースに投入するシードスクリプト（seed.py）を作成する。seed.py にはハードコードされたデータ定数を一切持たせず、全てのデータをExcelから動的に読み込む。

## 用語集

- **Seed_Script**: Excelファイルからデータを読み込みSQLiteデータベースに投入するPythonスクリプト（seed.py）
- **Excel_Source**: 設備マスタ・ステータス変更履歴・センサーデータを含むExcelファイル（sample_data.xlsx）
- **Factory_DB**: 設備データを格納するSQLiteデータベースファイル（data/factory.db）
- **Equipment_Table**: 設備マスタ情報を格納するデータベーステーブル（equipment）
- **Status_History_Table**: ステータス変更履歴を格納するデータベーステーブル（status_history）
- **Sensor_Data_Table**: センサー計測値を格納するデータベーステーブル（sensor_data）
- **DB_Schema**: Equipment_Table、Status_History_Table、Sensor_Data_Tableの定義を含むCREATE TABLE文の集合

## 要件

### 要件 1: ディレクトリ構成とプロジェクト構造

**ユーザーストーリー:** 開発者として、明確なディレクトリ構成を持つプロジェクトが欲しい。それにより、データ基盤のコードとデータファイルの配置を容易に把握できる。

#### 受け入れ基準

1. Seed_Script はプロジェクトルートに `seed.py` として配置されること
2. Factory_DB は `data/factory.db` に格納されること
3. Excel_Source はプロジェクトルートの `sample_data.xlsx` から読み込まれること
4. DB_Schema は `db/schema.sql` に独立したSQLファイルとして定義され、全てのCREATE TABLE文を含むこと

### 要件 2: DBスキーマ定義 — 設備マスタテーブル

**ユーザーストーリー:** 開発者として、Excelの設備マスタシートに対応するデータベーステーブルが欲しい。それにより、設備の基本情報をSQLで検索・集計できる。

#### 受け入れ基準

1. DB_Schema は Equipment_Table を以下のカラムで定義すること: `id` (INTEGER PRIMARY KEY), `name` (TEXT NOT NULL), `type` (TEXT NOT NULL), `location` (TEXT NOT NULL), `installed_date` (TEXT NOT NULL)
2. Equipment_Table の `id` にはExcelの行番号（1〜8）を使用し、他シートの「設備ID」との整合性を保つこと
3. Equipment_Table の全カラムに NOT NULL 制約を適用すること

### 要件 3: DBスキーマ定義 — ステータス変更履歴テーブル

**ユーザーストーリー:** 開発者として、Excelのステータス変更履歴シートに対応するデータベーステーブルが欲しい。それにより、各設備の稼働状態の変遷をSQLで追跡できる。

#### 受け入れ基準

1. DB_Schema は Status_History_Table を以下のカラムで定義すること: `id` (INTEGER PRIMARY KEY AUTOINCREMENT), `equipment_id` (INTEGER NOT NULL), `equipment_name` (TEXT NOT NULL), `occurred_at` (TEXT NOT NULL), `status_before` (TEXT NOT NULL), `status_after` (TEXT NOT NULL), `reason` (TEXT NOT NULL)
2. `equipment_id` に Equipment_Table(`id`) を参照する外部キー制約を定義すること
3. `equipment_id` カラムにインデックスを作成し、設備単位の検索を効率化すること

### 要件 4: DBスキーマ定義 — センサーデータテーブル

**ユーザーストーリー:** 開発者として、Excelのセンサーデータシートに対応するデータベーステーブルが欲しい。それにより、各設備のセンサー計測値を時系列で分析できる。

#### 受け入れ基準

1. DB_Schema は Sensor_Data_Table を以下のカラムで定義すること: `id` (INTEGER PRIMARY KEY AUTOINCREMENT), `equipment_id` (INTEGER NOT NULL), `timestamp` (TEXT NOT NULL), `temperature` (REAL NOT NULL), `vibration` (REAL NOT NULL), `rpm` (REAL), `power_kw` (REAL NOT NULL), `pressure` (REAL)
2. `equipment_id` に Equipment_Table(`id`) を参照する外部キー制約を定義すること
3. `rpm` と `pressure` カラムは NULL を許容し、該当センサーを持たない設備タイプに対応すること
4. `equipment_id` カラムにインデックス、および (`equipment_id`, `timestamp`) に複合インデックスを作成し、時系列クエリを効率化すること

### 要件 5: Excelデータ読み込みロジック

**ユーザーストーリー:** 開発者として、seed.pyがExcelファイルから全データを動的に読み込む仕組みが欲しい。それにより、ハードコードされたデータ定数なしでデータ投入を行える。

#### 受け入れ基準

1. Seed_Script は Excel_Source から全データを読み込み、ハードコードされたデータ定数を一切含まないこと
2. 設備マスタシートの読み込み時、Seed_Script は pandas ライブラリ（openpyxl エンジン）を使用し、4列（設備名, タイプ, 設置場所, 設置日）を全て読み込むこと
3. ステータス変更履歴シートの読み込み時、Seed_Script は 6列（設備ID, 設備名, 発生日時, 変更前ステータス, 変更後ステータス, 理由）を全て読み込むこと
4. センサーデータシートの読み込み時、Seed_Script は 7列（設備ID, タイムスタンプ, temperature, vibration, rpm, power_kw, pressure）を全て読み込むこと
5. Seed_Script は Excel_Source に定義されたシート名を使用して各シートを識別すること

### 要件 6: シードデータ投入ロジック

**ユーザーストーリー:** 開発者として、読み込んだExcelデータをSQLiteデータベースに正しく投入する仕組みが欲しい。それにより、ダッシュボードアプリがデータベースからデータを参照できる。

#### 受け入れ基準

1. Seed_Script 実行時、Factory_DB ファイルが存在しない場合は `data/factory.db` に新規作成すること
2. Seed_Script 実行時、`db/schema.sql` の DB_Schema を読み込み、`IF NOT EXISTS` 句を使用して全テーブルを作成すること
3. 設備マスタデータの投入時、行番号（1から開始）を各設備レコードの `id` 値として割り当てること
4. データ投入時、データベーストランザクションを使用し、全データ投入処理のアトミック性を保証すること
5. 既存の Factory_DB に対して Seed_Script を実行した場合、再投入前に全既存データをクリアし、冪等な実行を保証すること
6. Seed_Script はデータ投入前に SQLite 接続で外部キー制約を有効化すること

### 要件 7: データ整合性の検証

**ユーザーストーリー:** 開発者として、投入されたデータの整合性を検証する手段が欲しい。それにより、データ基盤が正しく構築されたことを確認できる。

#### 受け入れ基準

1. Seed_Script の実行完了時、各テーブル（Equipment_Table, Status_History_Table, Sensor_Data_Table）のレコード数を標準出力に表示すること
2. Seed_Script の実行完了時、Equipment_Table が 8件、Status_History_Table が 59件、Sensor_Data_Table が 1152件であることを検証すること
3. レコード数が期待値と一致しない場合、不一致を示す警告メッセージを表示すること

### 要件 8: エラーハンドリング

**ユーザーストーリー:** 開発者として、seed.py実行時のエラーが適切に処理される仕組みが欲しい。それにより、問題発生時に原因を特定しやすくなる。

#### 受け入れ基準

1. Excel_Source ファイルが指定パスに存在しない場合、説明的なエラーメッセージを表示し、非ゼロの終了コードで終了すること
2. テーブル作成またはデータ投入中にデータベースエラーが発生した場合、トランザクションをロールバックし、エラー詳細を表示し、非ゼロの終了コードで終了すること
3. Excel_Source のシート構造が想定と異なる場合（カラム不足）、不足カラムを特定する説明的なエラーメッセージを表示し、非ゼロの終了コードで終了すること
