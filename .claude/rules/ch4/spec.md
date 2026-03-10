---
paths:
  - "ch4/**/*"
---

# ch4: ruffによる静的解析改善 実装仕様

## 概要

ruff を使い、既存コードの lint 問題を修正し、フォーマットを統一する。

## ruff 設定（pyproject.toml）

```toml
[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "W", "B", "UP"]
```

### ルール説明

| ルール | 名称                 | 検出対象                   |
| ------ | -------------------- | -------------------------- |
| E      | pycodestyle errors   | 行長超過、空白ルール等     |
| F      | pyflakes             | 未使用import、未定義変数等 |
| I      | isort                | import文の順序             |
| W      | pycodestyle warnings | スタイル警告               |
| B      | flake8-bugbear       | よくあるバグパターン       |
| UP     | pyupgrade            | Python 3.12向けモダン構文  |

## 検出される問題

### I001: import順序

`db/connection.py` — stdlib の `from pathlib import Path` が third-party の `import pandas as pd` の後に配置されている。

### E501: 行長超過

`db/seed.py` — INSERT文が120文字を超過。文字列を分割して修正。

### B905: zip() に strict= パラメータがない

`pages/01_equipment_dashboard.py`、`tests/test_seed.py` — `zip()` に `strict=True` を追加。

## コマンド

```bash
# lint問題の検出
uv run ruff check .

# 自動修正（I001等）
uv run ruff check --fix .

# フォーマット
uv run ruff format .
```

## 検証

- `uv run ruff check .` がエラーなしで通ること
- `uv run ruff format --check .` が差分なしで通ること
- `uv run pytest -v` が全テストパスすること
