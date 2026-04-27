---
inclusion: auto
---

# 設備ダッシュボード UI仕様

## 1. ページ構成とファイル配置

```
app.py                              # エントリーポイント（st.set_page_config + リダイレクト）
pages/
  01_equipment_dashboard.py         # 設備ダッシュボードページ（メイン画面）
```

### app.py

- `st.set_page_config(page_title="設備ダッシュボード", page_icon="🔧", layout="wide")` を設定
- サイドバーに「設備ダッシュボード」のみ表示されるよう、app.py 自体は `st.switch_page("pages/01_equipment_dashboard.py")` でリダイレクトする
- これにより、サイドバーに "app" が表示されない

### pages/01_equipment_dashboard.py

- ダッシュボードの全UIを実装するメインページ
- 以下のセクションで構成される

## 2. UIコンポーネント詳細

### 2.1 サイドバー：設備選択ドロップダウン

- 配置: `st.sidebar`
- ラベル: `設備を選択`
- データソース: `equipment` テーブルから全設備の `id`, `name` を取得
- 表示形式: `st.selectbox` で設備名を表示、選択された設備のIDで以降のデータを絞り込む

### 2.2 設備情報カード

- 配置: ページ上部
- タイトル: `🔧 設備ダッシュボード`（`st.title`）
- レイアウト: `st.columns([2, 2, 1])` で3カラム構成
  - カラム1: `機種` → `equipment.equipment_type`、`設備場所` → `equipment.location`
  - カラム2: `設備情報`（セクションラベル）、現在のステータスを色付きインジケータで表示（`status_logs` の最新レコードの `new_status`）
  - カラム3: `設備ID` → `equipment.id`
- 各項目は `st.metric` または `st.markdown` で表示

### 2.3 センサーデータ推移セクション

#### 2.3.1 ゲージチャート（4つ）

- セクションタイトル: `センサーデータ推移`（`st.subheader`）
- レイアウト: `st.columns(4)` で横並び4つ
- 各ゲージの対象センサー:
  1. 温度（temperature）: 単位 `°C`
  2. 振動（vibration）: 単位 `mm/s`
  3. 回転数（rpm）: 単位 `rpm`
  4. 電力（power_kw）: 単位 `kW`
- チャートライブラリ: `plotly.graph_objects.Indicator` (mode="gauge+number")
- ゲージの色分け（3段階）:
  - 正常（緑）: 閾値未満
  - 警告（黄/オレンジ）: 閾値以上〜危険未満
  - 危険（赤）: 危険閾値以上
- 閾値設定（設備タイプ共通のデフォルト値）:

| センサー | 正常範囲 | 警告範囲 | 危険範囲 |
|---------|---------|---------|---------|
| temperature | 0〜80 | 80〜120 | 120〜300 |
| vibration | 0〜3.0 | 3.0〜5.0 | 5.0〜10.0 |
| rpm | 0〜1500 | 1500〜2000 | 2000〜3000 |
| power_kw | 0〜30 | 30〜40 | 40〜50 |

- 表示する値: 選択された設備の `sensor_readings` テーブルから最新のタイムスタンプのレコードを取得
- データが NULL の場合（例: CNC旋盤の pressure）: ゲージは表示するが値を 0 とし、「データなし」と注記

#### 2.3.2 時系列グラフ

- 配置: ゲージチャートの下
- チャートライブラリ: `plotly.graph_objects` の `Scatter` (mode="lines")
- X軸: タイムスタンプ（`sensor_readings.timestamp`）
- Y軸: 各センサー値
- 表示するセンサー: temperature, vibration, rpm, power_kw を1つのグラフに重ねて表示（マルチY軸またはサブプロット）
  - 実装方針: `plotly.subplots.make_subplots` で rows=2, cols=2 の4パネル構成とする
  - 各パネルに1センサーの時系列を表示
- データソース: 選択された設備の `sensor_readings` テーブルから全レコードを取得
- インタラクション: Plotly標準のホバーツールチップ（タイムスタンプと値を表示）
- 各パネルに警告・危険の閾値を水平線（`add_hline`）で表示:
  - 警告ライン: オレンジ色の破線
  - 危険ライン: 赤色の破線
- グラフの高さ: 500px

### 2.4 ステータス変更履歴テーブル

- セクションタイトル: `ステータス変更履歴`（`st.subheader`）
- 表示方法: `st.dataframe`
- データソース: `status_logs` テーブルから選択された設備のレコードを `timestamp DESC` で取得
- 表示カラム:

| 表示名 | DBカラム |
|-------|---------|
| 日時 | timestamp |
| 変更前 | old_status |
| 変更後 | new_status |
| 理由 | reason |

- カラム名は日本語に変換して表示（`pd.DataFrame.rename`）
- テーブルは `use_container_width=True` で全幅表示

## 3. 使用ライブラリ

| ライブラリ | 用途 | バージョン |
|-----------|------|-----------|
| streamlit | Webアプリフレームワーク | >=1.45.0 |
| pandas | データ操作 | >=2.2.0 |
| plotly | ゲージチャート・時系列グラフ | >=6.0.0 |
| sqlite3 | DB接続（標準ライブラリ） | - |

## 4. データソース

- DB: `data/factory.db`（SQLite）
- テーブル: `equipment`, `sensor_readings`, `status_logs`
- スキーマ: `db/schema.sql` に定義済み
- シードデータ: `db/seed.py` で `sample_data.xlsx` から投入済み