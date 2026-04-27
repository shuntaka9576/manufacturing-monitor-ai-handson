---
paths:
  - "ch5/**/*"
---

# ch5: PLaMo Embedding - 意味類似検索 実装仕様

## 追加ファイル

```
ch5/
├── db/
│   └── embed.py                    # Embedding生成・保存
├── pages/
│   └── 02_semantic_search.py       # 検索UIページ
└── (ch4の全ファイル。schema.sql のみ修正。seed.py は同一)
```

## 依存追加

```toml
dependencies = [
    "streamlit>=1.45.0",
    "pandas>=2.2.0",
    "plotly>=6.0.0",
    "openpyxl>=3.1.0",
    "torch",
    "transformers",
    "sentencepiece",
]
```

## スキーマ追加（schema.sql）

```sql
CREATE TABLE IF NOT EXISTS status_log_embeddings (
    status_log_id INTEGER PRIMARY KEY REFERENCES status_logs(id),
    embedding     BLOB NOT NULL
);
```

PLaMo Embedding の出力次元は 2048。numpy配列を `tobytes()` で保存。

## app.py の更新

`st.navigation` にページを追加。

```python
pg = st.navigation([
    st.Page("pages/01_equipment_dashboard.py", title="設備ダッシュボード", icon="🔧"),
    st.Page("pages/02_semantic_search.py", title="意味類似検索", icon="🔍"),
])
pg.run()
```

## seed.py

ch4 と同一。変更不要。`sample_data.xlsx` にステータス変更履歴が59件含まれており、意味類似検索に十分なデータ量がある。

## db/embed.py

```python
from transformers import AutoModel, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("pfnet/plamo-embedding-1b", trust_remote_code=True)
model = AutoModel.from_pretrained("pfnet/plamo-embedding-1b", trust_remote_code=True)
```

- `model.encode_document(texts, tokenizer)` でベクトル化
- `numpy.ndarray.tobytes()` で変換し `status_log_embeddings` に保存
- `reason` が NULL のレコードはスキップ

## pages/02_semantic_search.py

- `st.set_page_config` は不要（app.py の `st.navigation` で管理）
- `@st.cache_resource` でモデルキャッシュ
- `model.encode_query(query, tokenizer)` でクエリベクトル化
- `torch.nn.functional.cosine_similarity` で類似度計算
- 類似度閾値スライダー（0.0〜1.0、デフォルト0.3）
- 結果カラム: 類似度スコア(%)、設備名、日時、変更前→変更後、理由

## 検証

- 「振動の異常」→「ベアリング摩耗による振動増加」等が上位
- 「温度が高い」→「温度異常上昇を検知」等が上位
- 「定期点検」→「年次法定点検のため計画停止」等が上位
