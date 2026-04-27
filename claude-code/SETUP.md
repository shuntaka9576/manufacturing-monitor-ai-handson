# セットアップガイド（Claude Code 版）

このハンズオンを **Claude Code（CLI）** で進めるためのツールインストール手順です。macOS / Linux / Windows（WSL 推奨）を対象とします。

対象環境ごとに以下の手順ブロックを選んでください。

- **macOS**: Homebrew 前提の手順（macOS / Linux 共通ブロック）を実行
- **Linux**: apt / curl ベースの手順（macOS / Linux 共通ブロック）を実行
- **Windows (CMD / PowerShell)**: 各ツールの `Windows (CMD / PowerShell)` details を参照（CMD でも PowerShell でも実行可能）
- **WSL を使う場合**: 上記の **macOS / Linux 手順** をそのまま実行してください（WSL 内は Linux 環境です）

## 必要なツール

> 表の版で動作確認済み。新しい版での利用を推奨（厳密 pin は不要）。古い版でも動作する可能性はありますが未検証です。受講する章に応じて必要なものをインストールしてください。

| ツール                                                                | バージョン | 提供元                     | 用途                                         |
| --------------------------------------------------------------------- | ---------- | -------------------------- | -------------------------------------------- |
| [Python](https://www.python.org/)                                     | 3.12       | Python Software Foundation | 全章: アプリケーション実行                   |
| [uv](https://docs.astral.sh/uv/)                                      | 0.11       | Astral                     | 全章: Pythonパッケージ管理・タスク実行       |
| [Claude Code](https://docs.claude.com/en/docs/claude-code/quickstart) | 2.1.119    | Anthropic                  | 全章: AIコーディングエージェント             |
| [SQLite3](https://www.sqlite.org/)                                    | 3.x        | SQLite Consortium          | 全章: DBレコード確認                         |
| [spec-kit](https://github.com/github/spec-kit)                        | 0.8.0      | GitHub                     | ch1: Spec駆動スキル導入                      |
| [Node.js](https://nodejs.org/)                                        | 22         | OpenJS Foundation          | ch3-playwright: playwright CLI の実行        |
| [pnpm](https://pnpm.io/)                                              | 10.33.2    | pnpm                       | ch3-playwright: Node パッケージマネージャ    |
| [playwright-cli](https://github.com/microsoft/playwright-cli)         | 0.1.1      | Microsoft                  | ch3-playwright: ブラウザ自動操作             |
| [GitHub CLI](https://cli.github.com/)                                 | 2.90.0     | GitHub                     | ch3-skill-creator: `gh skill` で Skills 導入 |

## インストール手順

### 1. Python

macOS / Linux は既存のPythonで3.12以上を確認してください。Windowsはwingetでインストールします。

<details>
<summary>Windows (CMD / PowerShell)</summary>

```powershell
winget install -e --id Python.Python.3.12
```

</details>

```bash
python --version
# Python 3.12.x と表示されればOK
```

### 2. uv

2026-04-01 リリースの `0.11.3` を pin してインストールします。

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/0.11.3/install.sh | sh
```

<details>
<summary>Windows (CMD / PowerShell)</summary>

```powershell
# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.11.3/install.ps1 | iex"
```

</details>

インストール後、ターミナルを再起動してバージョンを確認します。

```bash
uv --version
# uv 0.11 系以上であればOK
```

### 3. Node.js

```bash
# macOS (Homebrew)
brew install node
```

<details>
<summary>Windows (CMD / PowerShell)</summary>

```powershell
winget install -e --id OpenJS.NodeJS.LTS
```

</details>

```bash
node --version
# v22.x.x 以上であればOK
```

### 4. Claude Code

公式インストーラで入れます。

```bash
# macOS / Linux
curl -fsSL https://claude.ai/install.sh | bash
```

<details>
<summary>Windows (CMD / PowerShell)</summary>

```powershell
powershell -Command "irm https://claude.ai/install.ps1 | iex"
```

</details>

動作確認します。

```bash
claude --version
# 2.1.119 で動作確認済み（最新版を推奨）
```

Claude Code を起動し、適当なプロンプトを送って応答が返ってくることを確認してください。

```bash
claude
```

### 5. SQLite3

```bash
# macOS (プリインストール済みの場合あり)
sqlite3 --version
```

<details>
<summary>Windows (CMD / PowerShell)</summary>

```powershell
winget install -e --id SQLite.SQLite
```

</details>

### 6. spec-kit

2026-04-23 リリースの `v0.8.0` を pin して `specify` CLI を `uv tool` で永続インストールします。

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.8.0
```

動作確認します。

```bash
specify --version
```

### 7. pnpm

2026-04-23 リリースの `10.33.2` を pin して公式スタンドアロンスクリプトでインストールします（pnpm 10 は `manage-package-manager-versions` で自己管理するため Corepack 不要）。

```bash
# macOS / Linux
curl -fsSL https://get.pnpm.io/install.sh | env PNPM_VERSION=10.33.2 sh -
```

<details>
<summary>Windows (CMD / PowerShell)</summary>

```powershell
powershell -Command "$env:PNPM_VERSION='10.33.2'; Invoke-WebRequest https://get.pnpm.io/install.ps1 -UseBasicParsing | Invoke-Expression"
```

</details>

動作確認します。

```bash
pnpm --version
# 10.33.2 と表示されればOK
```

### 8. playwright-cli

`playwright-cli` コマンドを提供する `@playwright/cli` と、ブラウザ／ffmpeg バイナリのインストーラを提供する `playwright` を pnpm でグローバルインストールします。

```bash
pnpm add -g @playwright/cli@0.1.1 playwright
```

ブラウザバイナリをインストールします。

```bash
playwright install
```

動画録画機能を使う場合は、ffmpeg も追加でインストールします。

```bash
playwright install ffmpeg
```

動作確認します。

```bash
playwright-cli --version
```

### 9. GitHub CLI

`gh skill` サブコマンドは Public Preview のため仕様変更の可能性があります。gh 本体を最新化します。

```bash
# macOS
brew upgrade gh
```

<details>
<summary>Windows (CMD / PowerShell)</summary>

```powershell
winget upgrade GitHub.cli
```

</details>

動作確認します。

```bash
gh --version
# 2.90.0 以上であればOK
```

GitHub に認証済みか確認します。

```bash
gh auth status
# Logged in to github.com ... と表示されればOK
```

未認証の場合は `gh auth login` を実行してください。

各チャプターの起動方法は [README.md](./README.md) のチャプター構成を参照してください。

## 付録: Pythonライブラリ一覧（参考情報）

各チャプターディレクトリで `uv sync` を実行すると自動インストールされるため、以下のライブラリを事前に手動インストールする必要はありません。何が入るかの参考情報として掲載しています。

| ライブラリ    | バージョン | ch1 | ch2 | ch3-playwright | ch3-skill-creator | ch4 | ch5 | 用途                        |
| ------------- | ---------- | --- | --- | -------------- | ----------------- | --- | --- | --------------------------- |
| streamlit     | >=1.45.0   | ✓   | ✓   | ✓              | ✓                 | ✓   | ✓   | UIフレームワーク            |
| pandas        | >=2.2.0    | ✓   | ✓   | ✓              | ✓                 | ✓   | ✓   | データフレーム処理          |
| plotly        | >=6.0.0    | ✓   | ✓   | ✓              | ✓                 | ✓   | ✓   | インタラクティブチャート    |
| openpyxl      | >=3.1.0    | ✓   | ✓   | ✓              | ✓                 | ✓   | ✓   | Excel読み込み               |
| pytest        | >=8.0.0    | ✓   | ✓   | ✓              | ✓                 | ✓   | ✓   | テスト実行                  |
| ruff          | >=0.11.0   |     |     |                |                   | ✓   | ✓   | リンター・フォーマッター    |
| torch         | 最新       |     |     |                |                   |     | ✓   | PyTorch（推論バックエンド） |
| transformers  | 最新       |     |     |                |                   |     | ✓   | Hugging Face Transformers   |
| sentencepiece | 最新       |     |     |                |                   |     | ✓   | トークナイザー              |

## 付録: サプライチェーンセキュリティ方針

ハンズオン中に OSS / npm パッケージを取り込む箇所では、以下の方針で版を固定し、リリース直後の悪性パッケージ取り込みを避けます。

- **Python ライブラリ**: 各チャプターの `uv.lock` に検証済みバージョンを記録。受講者は `uv sync` で同じ状態を再現できます
- **npm 経由ツール（playwright-cli 等）**: `@0.1.1` のように **バージョン pin** してインストール
- **Anthropic 公式プラグイン（ch3-skill-creator）**: Claude Code 公式マーケットプレイス経由で `/plugin marketplace add anthropics/skills` を登録し、`/plugin install skill-creator@anthropic-agent-skills` で取り込みます。配布元は Anthropic 公式リポジトリ（`anthropics/skills`）に限定され、必要に応じて `anthropics/skills#v1.0.0` のようにタグ指定でバージョン pin 可能です
- **ベースツール（Python / uv / Node.js / SQLite3 / GitHub CLI / Claude Code）**: 各プロジェクト公式のインストーラ／パッケージマネージャ経由のみを案内（環境差を避けるため厳密な pin は行いません）
