---
name: sync-chapters
description: 各章（ch1〜ch5_fin）の共有ファイルが正しく同期されているか検証し、不整合があれば修正する
allowed-tools: Bash, Read, Edit, Glob, Grep
---

各章間の共有ファイルの同期を検証し、不整合があれば修正してください。

## 章の進行と各ディレクトリの役割

- 各 `chN/` ディレクトリは章Nの演習の**開始時点**のファイルを含む
- 章Nの演習で作成されるファイルは `ch(N+1)/` の開始時点に含まれる
- `ch5_fin/` はch5の**完成形**（演習の出力結果）

## 共有ファイルの同期ルール

以下の各ペアで、記載されたファイルは完全に同一でなければならない。

| 比較                 | 同一であるべきファイル                                                                                                                     |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| ch1 → ch2                                     | `db/__init__.py`, `sample_data.xlsx`                                                                                                       |
| ch2 → ch3-playwright / ch3-skill-creator      | `db/__init__.py`, `db/schema.sql`, `db/seed.py`, `sample_data.xlsx`, `tests/__init__.py`, `tests/test_seed.py`                             |
| ch3-playwright ↔ ch3-skill-creator (Python側) | `app.py`, `db/connection.py`, `pages/01_equipment_dashboard.py`, `tests/__init__.py`, `tests/test_seed.py`, `db/schema.sql`, `db/seed.py`  |
| ch3-playwright / ch3-skill-creator → ch4      | 上記 + `app.py`, `db/connection.py`, `pages/01_equipment_dashboard.py`                                                                     |
| ch4 → ch5            | `sample_data.xlsx`, `db/__init__.py`, `db/schema.sql`, `tests/__init__.py` は同一。その他のPythonファイルはruff適用済みで差分あり          |
| ch5 → ch5_fin        | `db/seed.py`, `db/connection.py`, `pages/01_equipment_dashboard.py`, `tests/test_app.py`, `tests/test_connection.py`, `tests/test_seed.py` |

## ch4 → ch5 の期待差分（ruff適用）

ch4の演習（ruff check --fix + ruff format）により、ch5では以下のファイルにフォーマット・lint修正が適用されている。

- `app.py` — ruff format適用
- `db/connection.py` — import順序修正 (I001)
- `db/seed.py` — 行長修正 (E501)
- `pages/01_equipment_dashboard.py` — import順序修正、`zip()` に `strict=True` 追加
- `tests/test_seed.py` — `zip()` に `strict=True` 追加
- `tests/test_app.py` — ruff format適用
- `tests/test_connection.py` — ruff format適用（変更なしの場合もある）

## ch5_fin固有の差分（期待される差分）

ch5とch5_finで以下のファイルは差分があって正しい（ch5の演習の成果物）。

- `app.py` — セマンティック検索ページのエントリ追加
- `db/schema.sql` — `status_log_embeddings` テーブル追加
- `db/embed.py` — 新規（Embedding生成スクリプト）
- `pages/02_semantic_search.py` — 新規（意味類似検索ページ）
- `tests/test_semantic_search.py` — 新規（セマンティック検索のテスト）
- `pyproject.toml` — torch, transformers, sentencepiece 追加

## 各章に存在すべきファイル

| ディレクトリ | 含むべきファイル（README.md, pyproject.toml, data/factory.db 以外）                                                            |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| ch1          | `db/__init__.py`, `sample_data.xlsx`                                                                                           |
| ch2          | `dashbord.png`, `db/__init__.py`, `db/schema.sql`, `db/seed.py`, `sample_data.xlsx`, `tests/__init__.py`, `tests/test_seed.py` |
| ch3-playwright / ch3-skill-creator | ch2のファイル（`dashbord.png`除く） + `app.py`, `db/connection.py`, `pages/01_equipment_dashboard.py`。ch3-skill-creator には加えて `package.json`, `.npmrc`, `pnpm-lock.yaml`, `.gitignore` |
| ch4          | ch3のファイル + `tests/test_app.py`, `tests/test_connection.py`                                                                |
| ch5          | ch4と同じファイル構成（ソースはruff適用済み）                                                                                  |
| ch5_fin      | ch5のファイル + `db/embed.py`, `pages/02_semantic_search.py`, `tests/test_semantic_search.py`（schema.sql, app.pyは修正版）    |

## pyproject.toml の同期ルール

各チャプターの `pyproject.toml` は `name` と `description` 以外、以下の期待差分に従う。

### 期待される依存構成

| ライブラリ    | ch1 | ch2 | ch3 | ch4 | ch5 / ch5_fin |
| ------------- | --- | --- | --- | --- | ------------- |
| streamlit     | ✓   | ✓   | ✓   | ✓   | ✓             |
| pandas        | ✓   | ✓   | ✓   | ✓   | ✓             |
| plotly        | ✓   | ✓   | ✓   | ✓   | ✓             |
| openpyxl      | ✓   | ✓   | ✓   | ✓   | ✓             |
| pytest        | dev | dev | dev | dev | dev           |
| ruff          |     |     |     | dev | dev           |
| torch         |     |     |     |     | ✓             |
| transformers  |     |     |     |     | ✓             |
| sentencepiece |     |     |     |     | ✓             |

`✓` = `[project] dependencies`、`dev` = `[dependency-groups] dev`

### 期待される設定セクション

| セクション                  | ch1 | ch2 | ch3 | ch4 | ch5 / ch5_fin |
| --------------------------- | --- | --- | --- | --- | ------------- |
| `[tool.pytest.ini_options]` | ✓   | ✓   | ✓   | ✓   | ✓             |
| `[tool.ruff]`               |     |     |     | ✓   | ✓             |
| `[tool.ruff.lint]`          |     |     |     | ✓   | ✓             |

### 検証ルール

1. 上記マトリクスと各 `pyproject.toml` の内容が一致すること
2. 後続チャプターで依存が意図せず消えていないこと（共通ライブラリ4つは全チャプターに必須）
3. ch5 と ch5_fin は `name`, `description` 以外の依存・設定が同一であること

## チェック手順

1. 各章ペア間で共有ファイルを `diff` で比較する
2. 各章の `pyproject.toml` を上記マトリクスと照合する
3. 各章に存在すべきでないファイル（例: ch3にtests/が入っている）がないか確認する
4. 不整合があれば一覧で報告する
5. 修正方針: 下流の章（ch5_fin > ch5 > ch4 > ch3 > ch2 > ch1）を正とする。ただしch5_fin固有の差分は除く
6. ch4 → ch5 間はruff適用による差分が期待されるため、diffの内容がruff関連の変更のみかを確認する

## .kiro ディレクトリの同期ルール

各章の `.kiro/` ディレクトリも章の進行に従い同期する。

### 各章の .kiro 構成

| ディレクトリ | .kiro 内容                                                                                     |
| ------------ | ---------------------------------------------------------------------------------------------- |
| ch1          | 空サブディレクトリ（`specs/equipment-monitoring-seed/`, `steering/`）                          |
| ch2          | `steering/sample-data-structure.md`                                                            |
| ch3          | `steering/sample-data-structure.md`, `steering/dashboard-spec.md`                              |
| ch4          | ch3の`steering/` + `specs/ruff-code-quality/.config.kiro`, `specs/ruff-code-quality/bugfix.md` |
| ch5          | ch4と同一                                                                                      |
| ch5_fin      | ch5と同一                                                                                      |

### 同期ペア

| 比較                                          | 同一であるべき .kiro ファイル                                     |
| --------------------------------------------- | ----------------------------------------------------------------- |
| ch2 → ch3-playwright                          | `steering/sample-data-structure.md`                               |
| ch2 → ch3-skill-creator                       | `steering/sample-data-structure.md`                               |
| ch3-playwright ↔ ch3-skill-creator            | `steering/sample-data-structure.md`, `steering/dashboard-spec.md` |
| ch3-playwright / ch3-skill-creator → ch4      | `steering/sample-data-structure.md`, `steering/dashboard-spec.md` |
| ch4 → ch5            | `.kiro/` 配下すべて                                               |
| ch5 → ch5_fin        | `.kiro/` 配下すべて                                               |

## 除外対象

比較時に以下は無視する。

- `.venv/`, `__pycache__/`, `.pytest_cache/`, `.playwright-cli/`
- `*.lock`, `*.db`, `.DS_Store`
- `README.md`
