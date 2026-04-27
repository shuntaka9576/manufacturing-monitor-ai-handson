"""意味類似検索の期待結果テスト

PLaMo Embedding によるセマンティック検索が、期待するreasonテキストを
上位にヒットさせることを検証する。
"""

import sqlite3

import numpy as np
import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
from transformers import AutoModel, AutoTokenizer

from db.connection import DB_PATH

MODEL_NAME = "pfnet/plamo-embedding-1b"


@pytest.fixture(scope="module")
def model_and_tokenizer():
    """PLaMo モデルとトークナイザーをモジュールスコープでキャッシュ"""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    model = AutoModel.from_pretrained(MODEL_NAME, trust_remote_code=True, dtype=torch.float32)
    if not hasattr(model.config, "max_length"):
        model.config.max_length = model.config.max_position_embeddings
    return model, tokenizer


@pytest.fixture(scope="module")
def embeddings_from_db():
    """DBから全embeddingとreasonを読み込む"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT sle.status_log_id, sle.embedding, sl.reason
            FROM status_log_embeddings sle
            JOIN status_logs sl ON sle.status_log_id = sl.id
            """
        ).fetchall()
    except sqlite3.OperationalError:
        conn.close()
        pytest.skip("status_log_embeddingsテーブルが存在しません。embed.pyを実行してください")
    conn.close()
    if not rows:
        pytest.skip("embeddingデータがありません。embed.pyを実行してください")
    return [(row["reason"], np.frombuffer(row["embedding"], dtype=np.float32)) for row in rows]


def _search(query, model, tokenizer, embeddings, threshold=0.0):
    """クエリを実行し、(similarity, reason)のソート済みリストを返す"""
    with torch.no_grad():
        query_embedding = model.encode_query([query], tokenizer)
    query_tensor = query_embedding[0].detach().float()
    assert not torch.isnan(query_tensor).any(), f"クエリ '{query}' のembeddingがNaNです"

    results = []
    for reason, emb_np in embeddings:
        doc_tensor = torch.tensor(emb_np, dtype=torch.float32)
        sim = torch.nn.functional.cosine_similarity(query_tensor.unsqueeze(0), doc_tensor.unsqueeze(0)).item()
        if sim >= threshold:
            results.append((sim, reason))

    results.sort(key=lambda x: x[0], reverse=True)
    return results


def test_embeddings_exist():
    """embeddingデータが存在すること"""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        count = conn.execute("SELECT COUNT(*) FROM status_log_embeddings").fetchone()[0]
    except sqlite3.OperationalError:
        pytest.skip("status_log_embeddingsテーブルが存在しません。embed.pyを実行してください")
    conn.close()
    if count == 0:
        pytest.skip("status_log_embeddingsにデータがありません。embed.pyを実行してください")


@pytest.mark.parametrize(
    "query,expected_reason,max_rank",
    [
        ("油圧の圧力が下がった", "油圧圧力が規定値を下回る低下を検知", 1),
        ("冷却水の温度が高すぎる", "冷却水温度が上限値を超過", 1),
        ("金型交換", "新規金型セットアップのため停止", 1),
        ("材料不足", "材料補充のため一時停止", 1),
        ("温度が異常", "温度異常上昇を検知", 1),
        ("定期点検", "年次法定点検のため計画停止", 1),
        ("ロボットの位置がずれている", "ロボットアーム位置ずれを検知", 1),
        ("精度が悪い", "加工精度低下により調整停止", 5),
        ("品質に問題がある", "原材料品質不良によるロット停止", 5),
    ],
)
def test_semantic_search_expected_hit(query, expected_reason, max_rank, model_and_tokenizer, embeddings_from_db):
    """期待するreasonがmax_rank以内かつ閾値0.55以上でヒットすること"""
    model, tokenizer = model_and_tokenizer
    results = _search(query, model, tokenizer, embeddings_from_db)

    reasons_ranked = [reason for _, reason in results]
    assert expected_reason in reasons_ranked, f"'{expected_reason}' が結果に含まれていません"

    rank = reasons_ranked.index(expected_reason) + 1
    sim = results[rank - 1][0]

    assert rank <= max_rank, f"query='{query}': '{expected_reason}' は {rank}位 (期待: {max_rank}位以内)"
    assert sim >= 0.55, f"query='{query}': 類似度 {sim:.1%} が閾値 0.55 未満"
