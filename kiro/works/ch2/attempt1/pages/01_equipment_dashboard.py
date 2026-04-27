import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "factory.db"


def get_connection() -> sqlite3.Connection:
    """SQLite データベースへの接続を返す。"""
    return sqlite3.connect(str(DB_PATH))


@st.cache_data(ttl=60)
def fetch_equipment_list() -> pd.DataFrame:
    """設備一覧（id, name）を取得する。"""
    with get_connection() as conn:
        return pd.read_sql("SELECT id, name FROM equipment ORDER BY id", conn)


@st.cache_data(ttl=60)
def fetch_equipment_detail(equipment_id: int) -> pd.Series:
    """指定設備の詳細情報を取得する。"""
    with get_connection() as conn:
        df = pd.read_sql(
            "SELECT * FROM equipment WHERE id = ?", conn, params=(equipment_id,)
        )
    return df.iloc[0]


@st.cache_data(ttl=60)
def fetch_latest_sensor(equipment_id: int) -> pd.Series | None:
    """指定設備の最新センサーデータを取得する。"""
    with get_connection() as conn:
        df = pd.read_sql(
            "SELECT * FROM sensor_readings "
            "WHERE equipment_id = ? ORDER BY timestamp DESC LIMIT 1",
            conn,
            params=(equipment_id,),
        )
    if df.empty:
        return None
    return df.iloc[0]


@st.cache_data(ttl=60)
def fetch_sensor_history(equipment_id: int) -> pd.DataFrame:
    """指定設備のセンサーデータ全件を時系列順で取得する。"""
    with get_connection() as conn:
        return pd.read_sql(
            "SELECT timestamp, temperature, vibration, rpm, power_kw, pressure "
            "FROM sensor_readings WHERE equipment_id = ? ORDER BY timestamp",
            conn,
            params=(equipment_id,),
        )


@st.cache_data(ttl=60)
def fetch_status_logs(equipment_id: int) -> pd.DataFrame:
    """指定設備のステータス変更履歴を新しい順で取得する。"""
    with get_connection() as conn:
        return pd.read_sql(
            "SELECT timestamp, old_status, new_status, reason "
            "FROM status_logs WHERE equipment_id = ? ORDER BY timestamp DESC",
            conn,
            params=(equipment_id,),
        )


# --- サイドバー: 設備選択 ---
equipment_list = fetch_equipment_list()

selected_name = st.sidebar.selectbox(
    "設備を選択",
    equipment_list["name"].tolist(),
)

selected_id = int(
    equipment_list.loc[equipment_list["name"] == selected_name, "id"].iloc[0]
)

# --- データ取得 ---
equipment = fetch_equipment_detail(selected_id)
latest_sensor = fetch_latest_sensor(selected_id)
sensor_history = fetch_sensor_history(selected_id)
status_logs = fetch_status_logs(selected_id)

# --- 閾値定義 ---
THRESHOLDS = {
    "temperature": {
        "warn": 80,
        "danger": 120,
        "max": 300,
        "unit": "°C",
        "label": "温度",
    },
    "vibration": {
        "warn": 3.0,
        "danger": 5.0,
        "max": 10.0,
        "unit": "mm/s",
        "label": "振動",
    },
    "rpm": {
        "warn": 1500,
        "danger": 2000,
        "max": 3000,
        "unit": "rpm",
        "label": "回転数",
    },
    "power_kw": {"warn": 30, "danger": 40, "max": 50, "unit": "kW", "label": "電力"},
}

STATUS_COLORS = {
    "稼働中": "green",
    "停止中": "gray",
    "メンテナンス中": "orange",
    "異常": "red",
}

# --- Task 3: 設備情報カード ---
st.title("🔧 設備ダッシュボード")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    st.markdown("**機種**")
    st.write(equipment["equipment_type"])
    st.markdown("**設置場所**")
    st.write(equipment["location"])

with col2:
    st.markdown("**設備情報**")
    current_status = equipment["status"]
    color = STATUS_COLORS.get(current_status, "gray")
    st.markdown(f"現在のステータス: :{color}[●] {current_status}")

with col3:
    st.metric("設備ID", equipment["id"])

st.divider()

# --- Task 4: ゲージチャート ---
st.subheader("センサーデータ推移")

# 時系列グラフで選択された時刻のセンサー値を取得する
selected_ts = st.session_state.get("selected_sensor_ts")
if selected_ts is not None and not sensor_history.empty:
    matched = sensor_history[sensor_history["timestamp"] == selected_ts]
    gauge_source = matched.iloc[0] if not matched.empty else latest_sensor
else:
    gauge_source = latest_sensor
    selected_ts = None

# 選択中の時刻表示 & リセットボタン
if selected_ts is not None:
    ts_col, btn_col = st.columns([4, 1])
    with ts_col:
        st.caption(f"📌 表示中: {selected_ts}")
    with btn_col:
        if st.button("最新値に戻す"):
            del st.session_state["selected_sensor_ts"]
            st.rerun()
else:
    if latest_sensor is not None:
        st.caption(f"📌 表示中: 最新値 ({latest_sensor['timestamp']})")

gauge_cols = st.columns(4)
sensor_keys = ["temperature", "vibration", "rpm", "power_kw"]

for i, key in enumerate(sensor_keys):
    th = THRESHOLDS[key]
    value = 0.0
    no_data = True
    if gauge_source is not None and pd.notna(gauge_source.get(key)):
        value = float(gauge_source[key])
        no_data = False

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": f"{th['label']} ({th['unit']})"},
            gauge={
                "axis": {"range": [0, th["max"]]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, th["warn"]], "color": "#2ecc71"},
                    {"range": [th["warn"], th["danger"]], "color": "#f39c12"},
                    {"range": [th["danger"], th["max"]], "color": "#e74c3c"},
                ],
            },
        )
    )
    fig.update_layout(height=250, margin=dict(t=60, b=20, l=30, r=30))

    with gauge_cols[i]:
        st.plotly_chart(fig, use_container_width=True)
        if no_data:
            st.caption("データなし")

# --- Task 5: 時系列グラフ（クリックでゲージ連動） ---
if not sensor_history.empty:
    fig_ts = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[THRESHOLDS[k]["label"] for k in sensor_keys],
    )

    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]

    for idx, key in enumerate(sensor_keys):
        row, col = positions[idx]
        th = THRESHOLDS[key]

        fig_ts.add_trace(
            go.Scatter(
                x=sensor_history["timestamp"],
                y=sensor_history[key],
                mode="lines+markers",
                marker=dict(size=4),
                name=th["label"],
            ),
            row=row,
            col=col,
        )

        # 警告ライン
        fig_ts.add_hline(
            y=th["warn"],
            line_dash="dash",
            line_color="orange",
            row=row,
            col=col,
        )
        # 危険ライン
        fig_ts.add_hline(
            y=th["danger"],
            line_dash="dash",
            line_color="red",
            row=row,
            col=col,
        )

        # 選択中の時刻に赤マーカーを表示
        if selected_ts is not None:
            sel_row = sensor_history[sensor_history["timestamp"] == selected_ts]
            if not sel_row.empty and pd.notna(sel_row.iloc[0][key]):
                fig_ts.add_trace(
                    go.Scatter(
                        x=[selected_ts],
                        y=[float(sel_row.iloc[0][key])],
                        mode="markers",
                        marker=dict(size=12, color="red", symbol="circle"),
                        showlegend=False,
                        hoverinfo="skip",
                    ),
                    row=row,
                    col=col,
                )

    fig_ts.update_layout(height=500, showlegend=False)
    event = st.plotly_chart(
        fig_ts,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key="sensor_ts_chart",
    )

    # 選択イベントからタイムスタンプを取得して session_state に保存
    if event and event.selection and event.selection.points:
        clicked_x = event.selection.points[0].get("x", "")
        # Plotly は "2026-03-08 05:22:17" 形式で返すが、DB は "T" 区切り
        clicked_ts = clicked_x.replace(" ", "T")
        if clicked_ts and clicked_ts != st.session_state.get("selected_sensor_ts"):
            st.session_state["selected_sensor_ts"] = clicked_ts
            st.rerun()

st.divider()

# --- Task 6: ステータス変更履歴テーブル ---
st.subheader("ステータス変更履歴")

if not status_logs.empty:
    display_df = status_logs.rename(
        columns={
            "timestamp": "日時",
            "old_status": "変更前",
            "new_status": "変更後",
            "reason": "理由",
        }
    )
    st.dataframe(display_df, use_container_width=True)
else:
    st.info("ステータス変更履歴はありません。")
