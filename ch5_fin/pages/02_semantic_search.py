"""意味類似検索ページ - PLaMo Embeddingによるステータス変更履歴検索"""

import sqlite3

import numpy as np
import pandas as pd
import streamlit as st
import torch

from db.connection import DB_PATH

st.title("🔍 意味類似検索")

MODEL_NAME = "pfnet/plamo-embedding-1b"


@st.cache_resource
def load_model():
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    model = AutoModel.from_pretrained(MODEL_NAME, trust_remote_code=True, dtype=torch.float32)
    # transformers 5.x 互換: PlamoConfig に max_length がないため補完
    if not hasattr(model.config, "max_length"):
        model.config.max_length = model.config.max_position_embeddings
    return model, tokenizer


model, tokenizer = load_model()

PRESET_QUERIES = [
    "油圧の圧力が下がった",
    "冷却水の温度が高すぎる",
    "材料不足",
    "異音が発生している",
    "モーターが過熱している",
]

query = st.text_input(
    "検索クエリ",
    placeholder="例: 油圧の圧力が下がった、冷却水の温度が高すぎる",
    value=st.session_state.get("query_input", ""),
)
cols = st.columns(len(PRESET_QUERIES))
for i, preset in enumerate(PRESET_QUERIES):
    if cols[i].button(preset, use_container_width=True):
        st.session_state["query_input"] = preset
        st.rerun()

threshold = st.slider("類似度閾値", 0.0, 1.0, 0.3, 0.05)

if query:
    with torch.no_grad():
        query_embedding = model.encode_query([query], tokenizer)
    query_tensor = query_embedding[0].detach().float()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT
            sle.status_log_id,
            sle.embedding,
            sl.timestamp,
            sl.old_status,
            sl.new_status,
            sl.reason,
            e.name AS equipment_name
        FROM status_log_embeddings sle
        JOIN status_logs sl ON sle.status_log_id = sl.id
        JOIN equipment e ON sl.equipment_id = e.id
    """).fetchall()
    conn.close()

    if not rows:
        st.warning("Embeddingデータがありません。embed.py を実行してください。")
        st.stop()

    results = []
    for row in rows:
        emb = np.frombuffer(row["embedding"], dtype=np.float32)
        doc_tensor = torch.tensor(emb, dtype=torch.float32)
        similarity = torch.nn.functional.cosine_similarity(query_tensor.unsqueeze(0), doc_tensor.unsqueeze(0)).item()

        if similarity >= threshold:
            results.append(
                {
                    "類似度 (%)": round(similarity * 100, 1),
                    "設備名": row["equipment_name"],
                    "日時": row["timestamp"],
                    "変更": f"{row['old_status']} → {row['new_status']}",
                    "理由": row["reason"],
                }
            )

    if results:
        results_df = pd.DataFrame(results).sort_values("類似度 (%)", ascending=False)
        st.dataframe(results_df, width="stretch", hide_index=True)
        st.info(f"{len(results)} 件の結果が見つかりました。")
    else:
        st.info("該当する結果が見つかりませんでした。閾値を下げてみてください。")
