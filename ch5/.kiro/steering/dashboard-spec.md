---
inclusion: auto
---

# 設備ダッシュボード UI仕様

## 1. ページ構成とファイル配置

```
app.py                              # エントリーポイント（st.set_page_config + ナビゲーション）
pages/
  01_equipment_dashboard.py         # 設備ダッシュボードページ（メイン画面）
```

### app.py

- `st.set_page_config(page_title="設備モニタリング", page_icon="🏭", layout="wide")` を設定
- `st.navigation()` と `st.Page()` を使用してページナビゲーションを構成する
- `st.Page("pages/01_equipment_dashboard.py", title="設備ダッシュボード", icon="🔧")` でダッシュボードページを登録

### pages/01_equipment_dashboard.py

- ダッシュボードの全UIを実装するメインページ
- 以下のセクションで構成される

## 2. UIコンポーネント詳細

### 2.1 サイドバー：設備選択ドロップダウン

- 配置: `st.sidebar`
- ラベル: `設備を選択`
- データソース: `equipment` テーブルから全設備の `id`, `name`, `equipment_type`, `location`, `status` を取得
- 表示形式: `st.selectbox` で設備名を表示、選択された設備のIDで以降のデータを絞り込む

### 2.2 設備情報カード

- 配置: ページ上部
- タイトル: `🔧 設備ダッシュボード`（`st.title`）
- レイアウト: `st.columns(3)` で3カラム構成
  - カラム1: `種類` → `equipment.equipment_type`
  - カラム2: `設置場所` → `equipment.location`
  - カラム3: `設備ID` → `equipment.id`
- 各項目は `st.markdown` で表示

### 2.3 センサーデータ推移セクション

#### 2.3.1 ゲージチャート（動的）

- セクションタイトル: `センサーデータ推移`（`st.subheader`）
- レイアウト: `st.columns(len(available_params))` で利用可能なパラメータ数に応じた動的列数
- 対象センサー（設備タイプにより異なる）:
  - 温度（temperature）: 単位 `℃`
  - 振動（vibration）: 単位 `mm/s`
  - 回転数（rpm）: 単位 `RPM`
  - 電力（power_kw）: 単位 `kW`
  - 圧力（pressure）: 単位 `MPa`
- データが NULL または 0 のパラメータはゲージを表示しない
- チャートライブラリ: `plotly.graph_objects.Indicator` (mode="gauge+number")
- ゲージの色分け（3段階）:
  - 正常（緑 `#d4edda`）: 0〜warning
  - 警告（黄 `#fff3cd`）: warning〜critical
  - 危険（赤 `#f8d7da`）: critical〜max（critical × 1.5）
- 閾値設定（設備タイプ別、`db/connection.py` の `THRESHOLDS` 辞書で定義）:

**CNC旋盤:**

| センサー    | warning | critical |
| ----------- | ------- | -------- |
| temperature | 50      | 60       |
| vibration   | 3.5     | 4.5      |
| rpm         | 2400    | 2800     |
| power_kw    | 13      | 16       |

**プレス機:**

| センサー    | warning | critical |
| ----------- | ------- | -------- |
| temperature | 60      | 80       |
| vibration   | 7.0     | 9.0      |
| power_kw    | 55      | 70       |
| pressure    | 30      | 40       |

**射出成形機:**

| センサー    | warning | critical |
| ----------- | ------- | -------- |
| temperature | 240     | 270      |
| vibration   | 2.5     | 3.5      |
| power_kw    | 32      | 38       |
| pressure    | 130     | 160      |

**溶接ロボット:**

| センサー    | warning | critical |
| ----------- | ------- | -------- |
| temperature | 75      | 90       |
| vibration   | 4.5     | 6.0      |
| power_kw    | 26      | 32       |

- 表示する値: デフォルトは最新タイムスタンプのレコード。時系列グラフ上でポイントをクリックすると、その時刻の値に切り替わる
- 選択時刻の表示: `st.caption` で現在表示中の時刻を表示し、「最新値に戻す」ボタンで最新に復帰

#### 2.3.2 時系列グラフ

- 配置: ゲージチャートの下
- レイアウト: `st.tabs()` でセンサーパラメータごとにタブ切替
- チャートライブラリ: `plotly.graph_objects` の `Scatter` (mode="lines+markers")
- X軸: タイムスタンプ（`sensor_readings.timestamp`）
- Y軸: 各センサー値
- データソース: 選択された設備の `sensor_readings` テーブルから全レコードを取得
- インタラクション:
  - Plotly標準のホバーツールチップ（`hovermode="x unified"`）
  - ポイント選択（`on_select` + `selection_mode=["points"]`）でゲージの表示時刻を更新
  - 選択中の時刻に赤いマーカー（size=12）を表示
- 各タブに警告・危険の閾値を水平線（`add_hline`）で表示:
  - 警告ライン: オレンジ色（`#f39c12`）の破線、アノテーション「警告」
  - 危険ライン: 赤色（`#e74c3c`）の破線、アノテーション「危険」
- グラフの高さ: 400px

### 2.4 ステータス変更履歴テーブル

- セクションタイトル: `ステータス変更履歴`（`st.subheader`）
- 表示方法: `st.dataframe`
- データソース: `status_logs` テーブルから選択された設備のレコードを `timestamp DESC` で取得
- 表示カラム:

| 表示名 | DBカラム   |
| ------ | ---------- |
| 日時   | timestamp  |
| 変更前 | old_status |
| 変更後 | new_status |
| 理由   | reason     |

- カラム名はSQLのAS句で日本語に変換して表示
- テーブルは `use_container_width=True`, `hide_index=True` で全幅表示

## 3. 使用ライブラリ

| ライブラリ | 用途                         | バージョン |
| ---------- | ---------------------------- | ---------- |
| streamlit  | Webアプリフレームワーク      | >=1.45.0   |
| pandas     | データ操作                   | >=2.2.0    |
| plotly     | ゲージチャート・時系列グラフ | >=6.0.0    |
| sqlite3    | DB接続（標準ライブラリ）     | -          |

## 4. データソース

- DB: `data/factory.db`（SQLite）
- テーブル: `equipment`, `sensor_readings`, `status_logs`
- スキーマ: `db/schema.sql` に定義済み
- シードデータ: `db/seed.py` で `sample_data.xlsx` から投入済み
