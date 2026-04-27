"""PLaMo Embeddingによるステータス変更履歴のベクトル化スクリプト"""

import sqlite3
from pathlib import Path

import numpy as np
import torch

DB_PATH = Path(__file__).parent.parent / "data" / "factory.db"

MODEL_NAME = "pfnet/plamo-embedding-1b"


def _load_model():
    """PLaMo Embedding モデルをロードする。bfloat16 では NaN になるため float32 を使用。"""
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    model = AutoModel.from_pretrained(MODEL_NAME, trust_remote_code=True, dtype=torch.float32)

    # transformers 5.x 互換: PlamoConfig に max_length がないため補完
    if not hasattr(model.config, "max_length"):
        model.config.max_length = model.config.max_position_embeddings

    # NaN チェック: bfloat16 キャッシュ汚染でモデル出力が NaN になることがある
    with torch.no_grad():
        test = model.encode_document(["テスト"], tokenizer)
        if torch.isnan(test[0]).any():
            raise RuntimeError("モデル出力が NaN です。float32 ロードに失敗しています。")

    return model, tokenizer


def main() -> None:
    model, tokenizer = _load_model()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    rows = conn.execute("SELECT id, reason FROM status_logs WHERE reason IS NOT NULL").fetchall()

    if not rows:
        print("ベクトル化対象のレコードがありません。")
        conn.close()
        return

    ids = [row["id"] for row in rows]
    texts = [row["reason"] for row in rows]

    print(f"{len(texts)} 件のテキストをベクトル化中...")
    with torch.no_grad():
        embeddings = model.encode_document(texts, tokenizer)

    conn.execute("DELETE FROM status_log_embeddings")
    for log_id, emb in zip(ids, embeddings, strict=True):
        emb_bytes = emb.cpu().float().numpy().astype(np.float32).tobytes()
        conn.execute(
            "INSERT INTO status_log_embeddings (status_log_id, embedding) VALUES (?, ?)",
            (log_id, emb_bytes),
        )

    conn.commit()
    conn.close()
    print(f"{len(ids)} 件のEmbeddingを保存しました。")


if __name__ == "__main__":
    main()
