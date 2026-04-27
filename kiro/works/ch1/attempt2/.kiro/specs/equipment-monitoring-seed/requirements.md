# 要件定義書: 製造設備監視ダッシュボード データ基盤

## はじめに

製造設備の稼働状況をリアルタイムで監視するダッシュボードアプリのデータ基盤を構築する。Excel ファイル（sample_data.xlsx）から全データを読み込み、SQLite データベースへシードデータとして投入するスクリプト（seed.py）を提供する。ハードコードされたデータ定数は一切持たせず、Excel を唯一のデータソースとする。

## 用語集

- **Seed_Script**: Excel ファイルからデータを読み込み、SQLite データベースへ初期データを投入する Python スクリプト（seed.py）
- **Excel_Source**: 設備マスタ・ステータス変更履歴・センサーデータの3シートを含む Excel ファイル（sample_data.xlsx）
- **SQLite_DB**: アプリケーションのデータストアとなるファイルベースの SQLite データベース
- **設備マスタ_テーブル**: 工場設備の基本属性を格納するデータベーステーブル（equipment）
- **ステータス変更履歴_テーブル**: 設備の稼働状態の変遷を時系列で格納するデータベーステーブル（status_history）
- **センサーデータ_テーブル**: 設備のセンサー計測値を時系列で格納するデータベーステーブル（sensor_data）
- **設備ID**: 設備マスタの行インデックス（0始まり）+ 1 で算出される暗黙の識別子。他シートから参照される

## 要件

### 要件 1: ディレクトリ構成

**ユーザーストーリー:** 開発者として、プロジェクトのファイル配置が明確に定義されていることで、コードの管理と拡張を効率的に行いたい。

#### 受け入れ基準

1. THE Seed_Script SHALL プロジェクトルート直下の `db/` ディレクトリに配置される
2. THE SQLite_DB SHALL `db/` ディレクトリ内に `equipment_monitoring.db` というファイル名で生成される
3. THE Excel_Source SHALL プロジェクトルート直下に `sample_data.xlsx` として配置される
4. THE Seed_Script SHALL `db/seed.py` というファイルパスで配置される
5. THE Seed_Script SHALL DBスキーマ定義を `db/schema.sql` として外部ファイルに分離して管理する

### 要件 2: DBスキーマ定義

**ユーザーストーリー:** 開発者として、Excel のデータ構造を正確に反映したデータベーススキーマを持つことで、ダッシュボードアプリから効率的にデータを参照したい。

#### 受け入れ基準

1. THE SQLite_DB SHALL 設備マスタ_テーブル（equipment）を以下のカラムで定義する: id（INTEGER PRIMARY KEY）、name（TEXT NOT NULL）、type（TEXT NOT NULL）、location（TEXT NOT NULL）、installation_date（TEXT NOT NULL）
2. THE SQLite_DB SHALL ステータス変更履歴_テーブル（status_history）を以下のカラムで定義する: id（INTEGER PRIMARY KEY AUTOINCREMENT）、equipment_id（INTEGER NOT NULL）、equipment_name（TEXT NOT NULL）、occurred_at（TEXT NOT NULL）、status_before（TEXT NOT NULL）、status_after（TEXT NOT NULL）、reason（TEXT NOT NULL）、FOREIGN KEY (equipment_id) REFERENCES equipment(id)
3. THE SQLite_DB SHALL センサーデータ_テーブル（sensor_data）を以下のカラムで定義する: id（INTEGER PRIMARY KEY AUTOINCREMENT）、equipment_id（INTEGER NOT NULL）、timestamp（TEXT NOT NULL）、temperature（REAL）、vibration（REAL）、rpm（REAL）、power_kw（REAL）、pressure（REAL）、FOREIGN KEY (equipment_id) REFERENCES equipment(id)
4. THE SQLite_DB SHALL 外部キー制約を有効化した状態でデータベースを運用する
5. THE SQLite_DB SHALL センサーデータ_テーブルの rpm カラムと pressure カラムを NULL 許容とする（設備タイプにより計測されないセンサー値が存在するため）
6. THE SQLite_DB SHALL ステータス変更履歴_テーブルの equipment_id と occurred_at の組み合わせにインデックスを作成する
7. THE SQLite_DB SHALL センサーデータ_テーブルの equipment_id と timestamp の組み合わせにインデックスを作成する

### 要件 3: シードデータ投入ロジック

**ユーザーストーリー:** 開発者として、Excel ファイルから自動的にデータベースへ初期データを投入できることで、手動でのデータ入力作業を排除したい。

#### 受け入れ基準

1. THE Seed_Script SHALL Excel_Source の「設備マスタ」シートから全行を読み込み、設備マスタ_テーブルへ投入する
2. THE Seed_Script SHALL 設備マスタの行インデックス（0始まり）+ 1 を設備IDとして算出し、設備マスタ_テーブルの id カラムに設定する
3. THE Seed_Script SHALL Excel_Source の「ステータス変更履歴」シートから全行を読み込み、ステータス変更履歴_テーブルへ投入する
4. THE Seed_Script SHALL Excel_Source の「センサーデータ」シートから全行を読み込み、センサーデータ_テーブルへ投入する
5. THE Seed_Script SHALL ハードコードされたデータ定数を一切含まず、全てのデータを Excel_Source から読み込む
6. THE Seed_Script SHALL openpyxl ライブラリを使用して Excel ファイルを読み込む
7. THE Seed_Script SHALL データ投入前に既存のデータベースファイルが存在する場合、削除して再作成する
8. THE Seed_Script SHALL schema.sql ファイルを読み込んでテーブルを作成する
9. WHEN Excel_Source が存在しない場合, THEN THE Seed_Script SHALL エラーメッセージを表示して処理を終了する
10. WHEN Excel_Source のシート名が期待と異なる場合, THEN THE Seed_Script SHALL エラーメッセージを表示して処理を終了する
11. THE Seed_Script SHALL 全テーブルへのデータ投入を単一トランザクション内で実行する
12. WHEN データ投入中にエラーが発生した場合, THEN THE Seed_Script SHALL トランザクションをロールバックし、エラーメッセージを表示する
13. THE Seed_Script SHALL センサーデータの NaN 値を SQL の NULL として投入する

### 要件 4: 検証方法

**ユーザーストーリー:** 開発者として、シードデータの投入結果を簡単に検証できることで、データ基盤の正しさを確認したい。

#### 受け入れ基準

1. THE Seed_Script SHALL 投入完了後に各テーブルのレコード件数を標準出力に表示する（設備マスタ: 8件、ステータス変更履歴: 59件、センサーデータ: 1,152件）
2. THE Seed_Script SHALL `python db/seed.py` コマンドで実行可能である
3. THE Seed_Script SHALL 投入完了後に「シード完了」を示すメッセージを標準出力に表示する
4. WHEN 検証用の pytest テストが実行された場合, THE テスト SHALL 各テーブルのレコード件数が期待値と一致することを確認する
5. WHEN 検証用の pytest テストが実行された場合, THE テスト SHALL 設備マスタの設備IDが1〜8の連番であることを確認する
6. WHEN 検証用の pytest テストが実行された場合, THE テスト SHALL 外部キー制約が正しく機能していることを確認する
7. WHEN 検証用の pytest テストが実行された場合, THE テスト SHALL センサーデータの rpm カラムが CNC旋盤（設備ID 1,2）で NULL でないことを確認する
8. THE Seed_Script SHALL 検証用テストを `tests/test_seed.py` に配置する

### 要件 5: ラウンドトリップ整合性

**ユーザーストーリー:** 開発者として、Excel から DB へのデータ投入が情報の欠落なく行われることを保証したい。

#### 受け入れ基準

1. WHEN シードデータ投入が完了した場合, THE テスト SHALL Excel_Source の設備マスタの全行と設備マスタ_テーブルの全行が一致することを確認する（ラウンドトリップ検証）
2. WHEN シードデータ投入が完了した場合, THE テスト SHALL Excel_Source のステータス変更履歴の全行とステータス変更履歴_テーブルの全行が一致することを確認する
3. WHEN シードデータ投入が完了した場合, THE テスト SHALL Excel_Source のセンサーデータの全行とセンサーデータ_テーブルの全行が一致することを確認する（NaN は NULL として比較）
