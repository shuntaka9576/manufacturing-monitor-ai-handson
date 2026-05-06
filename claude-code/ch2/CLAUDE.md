## Output language

- 成果物（README.md / 計画文書など）は日本語で記述する。

## Command execution

- Python の実行・依存管理は必ず `uv` 経由で行う。`python3` / `python` を直接実行したり、`pip install` / `pip3 install` でライブラリを追加してはならない。
- スクリプト実行は `uv run python <path>`、テスト実行は `uv run pytest`、依存追加は `uv add <package>`、依存同期は `uv sync` を使う。
- 仮想環境は `uv` が管理する `.venv` のみを使い、`python -m venv` などで別の venv を作らない。
