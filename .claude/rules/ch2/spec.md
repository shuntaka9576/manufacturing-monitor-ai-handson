---
paths:
  - "ch2/**/*"
---

# ch2: 設備ダッシュボード - 実装仕様

## 追加ファイル

```
ch2/
├── app.py                              # st.navigation エントリーポイント
├── pages/
│   └── 01_equipment_dashboard.py       # 設備ダッシュボード
└── (ch1の全ファイル)
```

## データソース

### db.connection から利用する関数・定数

```python
from db.connection import query_df, STATUS_COLORS, THRESHOLDS, PARAM_LABELS
```

| シンボル                | 説明                                                                  |
| ----------------------- | --------------------------------------------------------------------- |
| `query_df(sql, params)` | SQLを実行し `pd.DataFrame` で返す                                     |
| `STATUS_COLORS`         | ステータス文字列 → hexカラーコードの辞書（例: `"稼働中": "#2ecc71"`） |
| `THRESHOLDS`            | 設備タイプ → パラメータ → `{warning, critical}` の閾値辞書            |
| `PARAM_LABELS`          | パラメータ英名 → 日本語ラベル（例: `"temperature": "温度 (℃)"`）      |

### SQLクエリ

| 用途           | クエリ                                                                                                                                                 |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 設備一覧       | `SELECT id, name, equipment_type, location, status FROM equipment`                                                                                     |
| センサーデータ | `SELECT * FROM sensor_readings WHERE equipment_id = ? ORDER BY timestamp`                                                                              |
| ステータス履歴 | `SELECT timestamp AS 日時, old_status AS 変更前, new_status AS 変更後, reason AS 理由 FROM status_logs WHERE equipment_id = ? ORDER BY timestamp DESC` |

ステータス履歴は日本語カラムエイリアスで取得し、そのまま `st.dataframe` で表示する。

## エントリーポイント（app.py）

`st.navigation` で pages 配下のページを登録するだけのシンプルなファイル。

- `st.set_page_config`: page_title="設備モニタリング", page_icon="🏭", layout="wide"
- `st.Page`: title="設備ダッシュボード", icon="🔧"
- サイドバーには「設備ダッシュボード」のみ表示（"app" は表示されない）

## 設備ダッシュボード（pages/01_equipment_dashboard.py）

### ページ全体構造

```
st.title("🔧 設備ダッシュボード")
サイドバー設備選択
設備情報カード（4列）
st.divider()
st.subheader("センサーデータ推移")
  ゲージチャート
  時系列チャート（タブ）
st.divider()
st.subheader("ステータス変更履歴")
  履歴テーブル
```

### 空データハンドリング

以下の3箇所でガード処理を行い、`st.stop()` で以降の処理を中断する。

1. 設備データ取得後: `equipment_df.empty` → `st.warning("設備データがありません。seed.py を実行してください。")`
2. センサーデータ取得後: `sensor_df.empty` → `st.info("この設備のセンサーデータはありません。")`
3. 利用可能パラメータ判定後: パラメータなし → `st.info("表示可能なセンサーデータがありません。")`

### サイドバー設備選択

`st.sidebar.selectbox("設備を選択", ...)` で全設備名のリストから選択。選択された設備名で `equipment_df` をフィルタし、設備情報（id, equipment_type, location, status）を取得する。

### 設備情報カード

`st.columns(4)` で4列レイアウト。各列に `markdown()` で表示する。

| 列  | 内容       | 表示形式                                    |
| --- | ---------- | ------------------------------------------- |
| 1   | 種類       | `**種類**: {equipment_type}`                |
| 2   | 設置場所   | `**設置場所**: {location}`                  |
| 3   | ステータス | `**ステータス**: :{status_color}[{status}]` |
| 4   | 設備ID     | `**設備ID**: {id}`                          |

ステータス色は `STATUS_COLORS.get(status)` でhexカラーコードを取得し、Streamlitの `:{color}[text]` 記法で色付き表示する。

### 利用可能パラメータの判定

全センサーパラメータ候補（`temperature`, `vibration`, `rpm`, `power_kw`, `pressure`）のうち、センサーデータにNaN以外かつ0以外の値が1件でも存在するパラメータのみを利用可能と判定する。

```python
available_params = [p for p in ["temperature", "vibration", "rpm", "power_kw", "pressure"]
                    if sensor_df[p].notna().any() and (sensor_df[p] != 0).any()]
```

これにより、CNC旋盤のrpmやプレス機のpressureなど設備タイプ固有のパラメータが自動的に表示対象になる。

### session_state によるタイムスタンプ管理

- 設備ごとにキー `selected_ts_{equip_id}` で選択中のタイムスタンプを管理
- 初期値は `None`（最新値を表示）
- 時系列グラフのクリックで更新、「最新値に戻す」ボタンで `None` にリセットして `st.rerun()`

### ゲージチャート

- 表示値: デフォルトはセンサーデータの最終行（最新値）。時刻が選択されていればその行の値を使用
- `st.caption` で「選択時刻: {ts}」または「最新値: {ts}」を表示
- 選択中は「最新値に戻す」ボタンを表示
- カラム数: `st.columns(len(gauge_params))` でパラメータ数に応じて動的に生成
- 各ゲージは `plotly.graph_objects.Indicator` (mode="gauge+number")
- ゲージ範囲: 0 〜 `threshold["critical"] * 1.5`
- 3色ステップ: 正常(#d4edda) → 警告(#fff3cd) → 危険(#f8d7da)
- バー色: #1f77b4
- 閾値マーカー: critical値の位置に赤線（gauge の threshold プロパティ）
- レイアウト: height=250, margin(t=60, b=20, l=30, r=30)

設備タイプごとの閾値は `THRESHOLDS[equipment_type][param]` で参照する。

**CNC旋盤**

| パラメータ  | warning | critical |
| ----------- | ------- | -------- |
| temperature | 50      | 60       |
| vibration   | 3.5     | 4.5      |
| rpm         | 2400    | 2800     |
| power_kw    | 13      | 16       |

**プレス機**

| パラメータ  | warning | critical |
| ----------- | ------- | -------- |
| temperature | 60      | 80       |
| vibration   | 7.0     | 9.0      |
| power_kw    | 55      | 70       |
| pressure    | 30      | 40       |

**射出成形機**

| パラメータ  | warning | critical |
| ----------- | ------- | -------- |
| temperature | 240     | 270      |
| vibration   | 2.5     | 3.5      |
| power_kw    | 32      | 38       |
| pressure    | 130     | 160      |

**溶接ロボット**

| パラメータ  | warning | critical |
| ----------- | ------- | -------- |
| temperature | 75      | 90       |
| vibration   | 4.5     | 6.0      |
| power_kw    | 26      | 32       |

### 時系列チャート

- `st.tabs()` でパラメータ別タブ。タブラベルは `PARAM_LABELS` の日本語名を使用
- 各タブ内に Plotly 折れ線グラフ（`go.Scatter`, mode="lines"）
- 線色: #1f77b4, 線幅: 2
- 警告閾値の破線（オレンジ #f39c12、`annotation_text="警告"`）
- 危険閾値の破線（赤 #e74c3c、`annotation_text="危険"`）
- 選択中の時刻がある場合、その時刻に赤マーカー（size=12, symbol="circle"）を追加
- レイアウト: height=400, margin(t=20, b=40, l=60, r=20), hovermode="x unified", **dragmode="select"**

```python
event = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    selection_mode=["points"],
    key=f"chart_{equip_id}_{param}",
)
```

- イベント処理: `event.selection.points[0].get("x")` でタイムスタンプを取得
- 現在の session_state と異なる場合のみ更新して `st.rerun()`

### ステータス変更履歴

- `st.subheader("ステータス変更履歴")`
- 日本語エイリアス付きSQLで取得した DataFrame を `st.dataframe(use_container_width=True, hide_index=True)` で表示
- データなしの場合は `st.info` で案内

## 検証

- サイドバーに「設備ダッシュボード」のみ表示される（"app" が表示されない）
- 射出成形機 C-02 → 直近3時間の温度・振動上昇が確認できる
- CNC旋盤 → rpmゲージ/タブが表示、プレス機 → pressureゲージ/タブが表示
- 時系列グラフのデータ点をクリックするとゲージが更新される
