# 製造設備モニタリングダッシュボード - AI駆動開発ハンズオン

製造業向け設備稼働状況可視化アプリを、AI駆動開発の手法で段階的に構築するハンズオン教材です。

Kiro IDE 版と Claude Code（CLI）版の両方を用意しています。どちらのツールで進めるかを最初に選び、以降は同じ系統（`*.kiro.md` もしくは `*.claude.md`）を読んでください。

## セットアップ

必要なツールとインストール手順は、使うAIツールに対応する方を参照してください。

- [Kiro 版セットアップガイド](./SETUP.kiro.md)
- [Claude Code 版セットアップガイド](./SETUP.claude.md)

## チャプター構成

各チャプターは独立した uv プロジェクトです。チャプターディレクトリを直接開いて演習します。

各チャプターの完成形が次のチャプターの開始状態になるプログレッシブ構成です。

| チャプター            | 内容                                  | 所要時間 |
| --------------------- | ------------------------------------- | -------- |
| ch1                   | Spec駆動開発                          | 約1時間  |
| ch2                   | Plan then Execute                     | 約1時間  |
| ch3-playwright        | Agent Skills（playwright-cli）        | 約30分   |
| ch3-skill-creator     | Agent Skills（skill-creator, 安全系） | 約50分   |
| ch4                   | ruffによる静的解析改善                | 約15分   |
| ch5                   | PLaMo Embedding                       | 応用編   |

> [!NOTE]
> ch3 は用途に応じて選んでください。**ch3-playwright** はブラウザ自動操作を学ぶ章ですが、企業のセキュリティポリシーでブラウザ自動操作が許可されない場合があります。その場合は **ch3-skill-creator** を選んでください（pnpm + `minimum-release-age` によるサプライチェーン防御を含む、`skill-creator` で自作スキルを育てる構成）。どちらを選んでも ch4 の開始状態（ch2 完成コード）に到達します。

全体像はこちら

![全体像](assets/root/all.png)

> [!NOTE]
> 本ハンズオン全体で約100クレジットを使用します。

> [!WARNING]
> 各チャプターは続きから行うことを推奨します。これはLLMが非決定的な出力をした結果として進行が詰まる可能性があるためです。ご了承ください。

### ch1: Spec駆動開発 - プロジェクト基盤 & DB（所要時間: 約1時間）

**AI手法**: Spec駆動開発（Kiro版: Spec モード、Claude Code 版: [spec-kit](https://github.com/github/spec-kit)）

- [Kiro 版](./ch1/README.kiro.md)
- [Claude Code 版](./ch1/README.claude.md)

DB スキーマとシードデータ生成の基盤を作成します。Spec ファイルに要件を記述し、AIにコードを生成させます。

**開始状態**: `pyproject.toml` + 仕様書のみ（コードなし）
**完成形**: → ch2 の開始状態

```bash
cd ch1
# Kiro もしくは Claude Code で開いて演習を実施
```

### ch2: Plan then Execute - ダッシュボード & 設備詳細ページ（所要時間: 約1時間）

**AI手法**: Plan then Execute（Kiro版: Vibe モードで計画→実装、Claude Code 版: ネイティブ プランモード）

- [Kiro 版](./ch2/README.kiro.md)
- [Claude Code 版](./ch2/README.claude.md)

KPI 指標、設備一覧テーブル、ステータス分布チャート、設備詳細ページを含むダッシュボードを作成します。

**開始状態**: ch1完成コード（DB基盤）
**完成形**: → ch3-playwright の開始状態

```bash
cd ch2 && uv sync
uv run python db/seed.py
uv run streamlit run app.py
```

### ch3-playwright: Agent Skills - playwright-cliによるUI動作確認（所要時間: 約30分）

**AI手法**: Agent Skills（playwright-cli スキル）

- [Kiro 版](./ch3-playwright/README.kiro.md)
- [Claude Code 版](./ch3-playwright/README.claude.md)

Agent Skills で playwright-cli スキルを導入し、ブラウザ自動操作によるUI動作確認を体験します。

**開始状態**: ch2完成コード（DB + UI）
**完成形**: → ch4 の開始状態

```bash
cd ch3-playwright && uv sync
uv run python db/seed.py
uv run streamlit run app.py
```

### ch3-skill-creator: Agent Skills - skill-creator によるスキル開発（所要時間: 約50分）

**AI手法**: Agent Skills（`vercel-labs/skills` CLI + Anthropic 公式 `skill-creator` + `claude-code-guide` / `AskUserQuestion`）

- [Kiro 版](./ch3-skill-creator/README.kiro.md)
- [Claude Code 版](./ch3-skill-creator/README.claude.md)

pnpm + `minimum-release-age=30240`（21日）で `skills` CLI をセキュアに固定導入。`anthropics/skills` から `skill-creator` を取り込み、設備稼働日報スキル `daily-operations-report` を対話で作成・Progressive Disclosure で改善します。さらに **組み込みサブエージェント `claude-code-guide` での仕様調査** と **`AskUserQuestion` でのスキル対話化** も重ね、Agent Skills の実運用感覚を一通り体験できる構成です。ブラウザ自動操作を避けたい環境向けの ch3 代替コースでもあります。

**開始状態**: ch2完成コード（DB + UI）
**完成形**: → ch4 の開始状態

```bash
cd ch3-skill-creator && uv sync
uv run python db/seed.py
uv run streamlit run app.py

# 別ターミナル
cd ch3-skill-creator && pnpm install
pnpm exec -- skills add anthropics/skills --skill skill-creator -a claude-code -y
```

### ch4: ruffによる静的解析改善（所要時間: 約15分）

**AI手法**: 任意（プロンプトのみ。Kiro でも Claude Code でも可）

- [Kiro 版](./ch4/README.kiro.md)
- [Claude Code 版](./ch4/README.claude.md)

ruff を使い、既存コードの品質を静的解析で改善します。

**開始状態**: ch3-playwright もしくは ch3-skill-creator の完成コード（DB + UI）
**完成形**: → ch5 の開始状態

```bash
cd ch4 && uv sync
uv run ruff check .
```

### ch5: PLaMo Embedding - 意味類似検索（応用編）

**AI手法**: 任意（プロンプトのみ。Kiro でも Claude Code でも可）

- [Kiro 版](./ch5/README.kiro.md)
- [Claude Code 版](./ch5/README.claude.md)

PLaMo Embedding を使い、ステータス変更履歴を自然言語で意味類似検索できるページを追加します。

**開始状態**: ch4完成コード（DB + UI + テスト + ruff適用済み）
**完成形**: → fin

```bash
cd ch5 && uv sync
uv run python db/seed.py
uv run python db/embed.py
uv run streamlit run app.py
```
