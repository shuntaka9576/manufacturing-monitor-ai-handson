# 製造設備モニタリングダッシュボード - AI駆動開発ハンズオン

製造業向け設備稼働状況可視化アプリを、AI駆動開発の手法で段階的に構築するハンズオン教材です。

## セットアップ

必要なツールとインストール手順は[セットアップガイド](./SETUP.md)を参照してください。

## チャプター構成

各チャプターは独立した uv プロジェクトです。Kiroでchapterディレクトリを直接開いて演習します。

各チャプターの完成形が次のチャプターの開始状態になるプログレッシブ構成です。

| チャプター | 内容                   | 所要時間 |
| ---------- | ---------------------- | -------- |
| ch1        | Spec駆動開発           | 約1時間  |
| ch2        | Plan then Execute      | 約1時間  |
| ch3        | Agent Skills           | 約30分   |
| ch4        | ruffによる静的解析改善 | 約15分   |
| ch5        | PLaMo Embedding        | 応用編   |

全体像はこちら

![全体像](../assets/root/all.png)

> [!NOTE]
> 本ハンズオン全体で約100クレジットを使用します。

> [!WARNING]
> 各チャプターは続きから行うことを推奨します。これはLLMが非決定的な出力をした結果として進行が詰まる可能性があるためです。ご了承ください。

### [ch1: Spec駆動開発 - プロジェクト基盤 & DB](./ch1/README.md)（所要時間: 約1時間）

**AI手法**: Kiroの Spec駆動開発

DB スキーマとシードデータ生成の基盤を作成します。Spec ファイルに要件を記述し、Kiro にコードを生成させます。

**開始状態**: `pyproject.toml` + 仕様書のみ（コードなし）
**完成形**: → ch2 の開始状態

```bash
cd ch1
# Kiroで開いて演習を実施
```

### [ch2: Plan then Execute - ダッシュボード & 設備詳細ページ](./ch2/README.md)（所要時間: 約1時間）

**AI手法**: Kiroの Plan then Execute

KPI 指標、設備一覧テーブル、ステータス分布チャート、設備詳細ページを含むダッシュボードを作成します。

**開始状態**: ch1完成コード（DB基盤）
**完成形**: → ch3 の開始状態

```bash
cd ch2 && uv sync
uv run python db/seed.py
uv run streamlit run app.py
```

### [ch3: Agent Skills - playwright-cliによるUI動作確認](./ch3/README.md)（所要時間: 約30分）

**AI手法**: Agent Skills（playwright-cli）

Agent Skillsでplaywright-cliスキルを導入し、ブラウザ自動操作によるUI動作確認を体験します。

**開始状態**: ch2完成コード（DB + UI）
**完成形**: → ch4 の開始状態

```bash
cd ch3 && uv sync
uv run python db/seed.py
uv run streamlit run app.py
```

### [ch4: ruffによる静的解析改善](./ch4/README.md)（所要時間: 約15分）

**AI手法**: Kiroで実装（手法は任意）

ruff を使い、既存コードの品質を静的解析で改善します。

**開始状態**: ch3完成コード（DB + UI + テスト）
**完成形**: → ch5 の開始状態

```bash
cd ch4 && uv sync
uv run ruff check .
```

### [ch5: PLaMo Embedding - 意味類似検索](./ch5/README.md)（応用編）

**AI手法**: Kiroで実装（手法は任意）

PLaMo Embedding を使い、ステータス変更履歴を自然言語で意味類似検索できるページを追加します。

**開始状態**: ch4完成コード（DB + UI + テスト + ruff適用済み）
**完成形**: → fin

```bash
cd ch5 && uv sync
uv run python db/seed.py
uv run python db/embed.py
uv run streamlit run app.py
```
