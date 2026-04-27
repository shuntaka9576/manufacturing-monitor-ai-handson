"""設備ダッシュボード - センサーデータ・ステータス履歴"""

import plotly.graph_objects as go
import streamlit as st

from db.connection import PARAM_LABELS, THRESHOLDS, query_df

st.title("🔧 設備ダッシュボード")

# --- サイドバー: 設備選択 ---
equipment_df = query_df("SELECT id, name, equipment_type, location, status FROM equipment")

if equipment_df.empty:
    st.warning("設備データがありません。seed.py を実行してください。")
    st.stop()

selected_name = st.sidebar.selectbox(
    "設備を選択",
    equipment_df["name"].tolist(),
)

selected = equipment_df[equipment_df["name"] == selected_name].iloc[0]
equip_id = int(selected["id"])

# --- 設備情報カード ---
info_col1, info_col2, info_col3 = st.columns(3)
info_col1.markdown(f"**種類**: {selected['equipment_type']}")
info_col2.markdown(f"**設置場所**: {selected['location']}")
info_col3.markdown(f"**設備ID**: {equip_id}")

st.divider()

# --- センサーデータ取得 ---
sensor_df = query_df(
    "SELECT * FROM sensor_readings WHERE equipment_id = ? ORDER BY timestamp",
    (equip_id,),
)

if sensor_df.empty:
    st.info("この設備のセンサーデータはありません。")
    st.stop()

# --- センサーデータ推移セクション ---
st.subheader("センサーデータ推移")

# 表示可能なパラメータを特定
available_params = [
    p
    for p in ["temperature", "vibration", "rpm", "power_kw", "pressure"]
    if sensor_df[p].notna().any() and (sensor_df[p] != 0).any()
]

if not available_params:
    st.info("表示可能なセンサーデータがありません。")
    st.stop()

# session_state で選択中のタイムスタンプを管理
state_key = f"selected_ts_{equip_id}"
if state_key not in st.session_state:
    st.session_state[state_key] = None

selected_ts = st.session_state[state_key]

# 選択中の時刻に対応するセンサー値を取得
if selected_ts is not None:
    normalized_ts = str(selected_ts).replace(" ", "T")
    matching = sensor_df[sensor_df["timestamp"] == normalized_ts]
    if not matching.empty:
        gauge_row = matching.iloc[0]
    else:
        gauge_row = sensor_df.iloc[-1]
        st.session_state[state_key] = None
else:
    gauge_row = sensor_df.iloc[-1]

# --- ゲージチャート（選択時刻のセンサー値） ---
ts_label = str(gauge_row["timestamp"])[:16]
if selected_ts is not None:
    st.caption(f"選択時刻: {ts_label}")
    if st.button("最新値に戻す"):
        st.session_state[state_key] = None
        st.rerun()
else:
    st.caption(f"最新値: {ts_label}")

gauge_params = [p for p in available_params if gauge_row[p] is not None and gauge_row[p] != 0]

if gauge_params:
    gauge_cols = st.columns(len(gauge_params))
    for col, param in zip(gauge_cols, gauge_params, strict=True):
        value = float(gauge_row[param])
        equip_thresholds = THRESHOLDS.get(selected["equipment_type"], {})
        threshold = equip_thresholds.get(param, {"warning": 50, "critical": 80})
        label = PARAM_LABELS.get(param, param)

        max_val = threshold["critical"] * 1.5

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=value,
                title={"text": label},
                gauge={
                    "axis": {"range": [0, max_val]},
                    "bar": {"color": "#1f77b4"},
                    "steps": [
                        {"range": [0, threshold["warning"]], "color": "#d4edda"},
                        {"range": [threshold["warning"], threshold["critical"]], "color": "#fff3cd"},
                        {"range": [threshold["critical"], max_val], "color": "#f8d7da"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 2},
                        "thickness": 0.75,
                        "value": threshold["critical"],
                    },
                },
            )
        )
        fig.update_layout(margin=dict(t=60, b=20, l=30, r=30), height=250)
        col.plotly_chart(fig, use_container_width=True)

# --- 時系列チャート（クリックでゲージ更新） ---
tab_labels = [PARAM_LABELS.get(p, p) for p in available_params]
tabs = st.tabs(tab_labels)

for tab, param in zip(tabs, available_params, strict=True):
    with tab:
        equip_thresholds = THRESHOLDS.get(selected["equipment_type"], {})
        threshold = equip_thresholds.get(param, {"warning": 50, "critical": 80})
        label = PARAM_LABELS.get(param, param)

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=sensor_df["timestamp"],
                y=sensor_df[param],
                mode="lines+markers",
                name=label,
                line={"color": "#1f77b4", "width": 2},
                marker={"size": 5, "color": "#1f77b4"},
            )
        )

        # 警告閾値ライン
        fig.add_hline(
            y=threshold["warning"],
            line_dash="dash",
            line_color="#f39c12",
            annotation_text="警告",
            annotation_position="top right",
        )

        # 危険閾値ライン
        fig.add_hline(
            y=threshold["critical"],
            line_dash="dash",
            line_color="#e74c3c",
            annotation_text="危険",
            annotation_position="top right",
        )

        # 選択中の時刻にマーカーを表示
        if selected_ts is not None:
            normalized_ts = str(selected_ts).replace(" ", "T")
            matching = sensor_df[sensor_df["timestamp"] == normalized_ts]
            if not matching.empty:
                fig.add_trace(
                    go.Scatter(
                        x=[selected_ts],
                        y=[float(matching.iloc[0][param])] if matching.iloc[0][param] is not None else [0],
                        mode="markers",
                        marker={"color": "red", "size": 12, "symbol": "circle"},
                        name="選択点",
                        showlegend=False,
                    )
                )

        fig.update_layout(
            xaxis_title="時刻",
            yaxis_title=label,
            height=400,
            margin=dict(t=20, b=40, l=60, r=20),
            hovermode="x unified",
        )

        chart_key = f"chart_{equip_id}_{param}"

        def _on_select(*, _key=chart_key, _state_key=state_key):
            ev = st.session_state[_key]
            if ev.selection and ev.selection.points:
                st.session_state[_state_key] = ev.selection.points[0]["x"]

        st.plotly_chart(
            fig,
            use_container_width=True,
            on_select=_on_select,
            selection_mode=["points"],
            key=chart_key,
        )

st.divider()

# --- ステータス変更履歴 ---
st.subheader("ステータス変更履歴")

status_df = query_df(
    """
    SELECT
        timestamp AS 日時,
        old_status AS 変更前,
        new_status AS 変更後,
        reason AS 理由
    FROM status_logs
    WHERE equipment_id = ?
    ORDER BY timestamp DESC
""",
    (equip_id,),
)

if status_df.empty:
    st.info("この設備のステータス変更履歴はありません。")
else:
    st.dataframe(status_df, use_container_width=True, hide_index=True)
