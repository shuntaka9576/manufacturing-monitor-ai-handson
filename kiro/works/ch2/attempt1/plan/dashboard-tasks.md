# 設備ダッシュボード 実装計画

## 作成するファイル一覧

| ファイル | 役割 |
|---|---|
| `app.py` | エントリーポイント。`st.set_page_config` を設定し、ダッシュボードページへリダイレクト |
| `pages/01_equipment_dashboard.py` | ダッシュボードのメインページ。設備選択・情報カード・ゲージチャート・時系列グラフ・ステータス履歴を表示 |

## 実装タスク

### Phase 1: エントリーポイント

- [x] **Task 1**: `app.py` を作成
  - `st.set_page_config(page_title="設備ダッシュボード", page_icon="🔧", layout="wide")` を設定
  - `st.switch_page("pages/01_equipment_dashboard.py")` でリダイレクト
  - 依存: なし

### Phase 2: ダッシュボードページ — データ取得とレイアウト骨格

- [x] **Task 2**: `pages/01_equipment_dashboard.py` の骨格を作成
  - DB接続ヘルパー（`data/factory.db` への接続）
  - サイドバーの設備選択ドロップダウン（`st.sidebar.selectbox`）
  - 選択された設備IDに基づくデータ取得関数（設備情報・最新センサー値・センサー時系列・ステータス履歴）
  - 依存: Task 1

### Phase 3: UIコンポーネント実装

- [x] **Task 3**: 設備情報カードの実装
  - `st.title("🔧 設備ダッシュボード")`
  - `st.columns([2, 2, 1])` で3カラムレイアウト
  - 機種・設置場所・現在ステータス（色付き）・設備IDを表示
  - 依存: Task 2

- [x] **Task 4**: ゲージチャート（4つ）の実装
  - `st.subheader("センサーデータ推移")`
  - `st.columns(4)` で temperature / vibration / rpm / power_kw のゲージを横並び表示
  - `plotly.graph_objects.Indicator`（mode="gauge+number"）を使用
  - 閾値に基づく3段階の色分け（緑・オレンジ・赤）
  - NULL値の場合は 0 表示 +「データなし」注記
  - 依存: Task 3

- [x] **Task 5**: 時系列グラフの実装
  - `plotly.subplots.make_subplots(rows=2, cols=2)` で4パネル構成
  - 各パネルに temperature / vibration / rpm / power_kw の折れ線グラフ
  - 警告ライン（オレンジ破線）・危険ライン（赤破線）を `add_hline` で追加
  - グラフ高さ 500px
  - 依存: Task 4

- [x] **Task 6**: ステータス変更履歴テーブルの実装
  - `st.subheader("ステータス変更履歴")`
  - `st.dataframe` で `timestamp DESC` 順に表示
  - カラム名を日本語に変換（日時・変更前・変更後・理由）
  - `use_container_width=True`
  - 依存: Task 5

## 依存関係（実装順序）

```
Task 1 (app.py)
  └─ Task 2 (ページ骨格・データ取得)
       └─ Task 3 (設備情報カード)
            └─ Task 4 (ゲージチャート)
                 └─ Task 5 (時系列グラフ)
                      └─ Task 6 (ステータス履歴テーブル)
```

Task 1 → 2 → 3 → 4 → 5 → 6 の順に実装する。各タスク完了後にチェックを入れて進捗を管理する。
