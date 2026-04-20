# セットアップガイド（Claude Code 版）

このハンズオンを **Claude Code（CLI）** で進めるためのツールインストール手順です。macOS / Linux / Windows（WSL 推奨）を対象とします。

Kiro IDE で進めたい方は [SETUP.kiro.md](./SETUP.kiro.md) を参照してください。

## 必須ツール（全チャプター共通）

| ツール                                                                | バージョン | 提供元                     | 用途                             |
| --------------------------------------------------------------------- | ---------- | -------------------------- | -------------------------------- |
| [Python](https://www.python.org/)                                     | 3.12以上   | Python Software Foundation | アプリケーション実行             |
| [uv](https://docs.astral.sh/uv/)                                      | 0.10.4     | Astral                     | Pythonパッケージ管理・タスク実行 |
| [Node.js](https://nodejs.org/)                                        | 22以上     | OpenJS Foundation          | Claude Code 本体の実行           |
| [Claude Code](https://docs.claude.com/en/docs/claude-code/quickstart) | 最新       | Anthropic                  | AIコーディングエージェント       |
| [SQLite3](https://www.sqlite.org/)                                    | 3.x        | SQLite Consortium          | DBレコード確認                   |

## チャプター別の追加ツール

| ツール                                                        | 対象チャプター | 提供元    | 用途               |
| ------------------------------------------------------------- | -------------- | --------- | ------------------ |
| [spec-kit](https://github.com/github/spec-kit)                | ch1            | GitHub    | Spec駆動スキル導入 |
| [playwright-cli](https://github.com/microsoft/playwright-cli) | ch3-playwright | Microsoft | ブラウザ自動操作   |

### Pythonライブラリ一覧

各チャプターディレクトリで `uv sync` を実行すると自動インストールされます（Kiro 版と同じ）。

| ライブラリ    | バージョン | ch1 | ch2 | ch3-playwright | ch4 | ch5 | 用途                        |
| ------------- | ---------- | --- | --- | -------------- | --- | --- | --------------------------- |
| streamlit     | >=1.45.0   | ✓   | ✓   | ✓              | ✓   | ✓   | UIフレームワーク            |
| pandas        | >=2.2.0    | ✓   | ✓   | ✓              | ✓   | ✓   | データフレーム処理          |
| plotly        | >=6.0.0    | ✓   | ✓   | ✓              | ✓   | ✓   | インタラクティブチャート    |
| openpyxl      | >=3.1.0    | ✓   | ✓   | ✓              | ✓   | ✓   | Excel読み込み               |
| pytest        | >=8.0.0    | ✓   | ✓   | ✓              | ✓   | ✓   | テスト実行                  |
| ruff          | >=0.11.0   |     |     |                | ✓   | ✓   | リンター・フォーマッター    |
| torch         | 最新       |     |     |                |     | ✓   | PyTorch（推論バックエンド） |
| transformers  | 最新       |     |     |                |     | ✓   | Hugging Face Transformers   |
| sentencepiece | 最新       |     |     |                |     | ✓   | トークナイザー              |

## インストール手順

### 1. Python

macOS / Linux は既存のPythonで3.12以上を確認してください。Windowsはwingetでインストールします。

```powershell
winget install -e --id Python.Python.3.12
```

```bash
python --version
# Python 3.12.x と表示されればOK
```

### 2. uv

公式インストーラで入れます。

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/0.10.4/install.sh | sh
```

```powershell
# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.10.4/install.ps1 | iex"
```

インストール後、ターミナルを再起動してバージョンを確認します。

```bash
uv --version
# uv 0.10.4 と表示されればOK
```

### 3. Node.js

Claude Code の実行に必要です。

```bash
# macOS (Homebrew)
brew install node

# Windows
winget install -e --id OpenJS.NodeJS.LTS
```

```bash
node --version
# v22.x.x 以上であればOK
```

### 4. Claude Code

npm でグローバルインストールします。

```bash
npm install -g @anthropic-ai/claude-code
```

動作確認します。

```bash
claude --version
```

#### 4.1. 初回ログイン

Claude Code を起動してログインします。

```bash
claude
```

起動後、スラッシュコマンドで初期設定を行います。

```text
/login        # ブラウザ経由で Anthropic アカウントにログイン
/status       # プラン（Pro / Max / API）とログイン状態を確認
/model        # モデルを選択（Opus / Sonnet）
```

> [!NOTE]
> 本ハンズオンでは、仕様作成など思考が必要なステップで Opus を、ルーチンなタスク実行で Sonnet を使います。`/model` で随時切り替えてください。

#### 4.2. チャット動作確認

プロンプト欄に「こんにちは」などを入力し、応答が返ることを確認してください。

> 生成AIへリクエストが正常に送信できるかの確認です。

#### 4.3. プランモードの確認

`Shift+Tab` で「plan mode」と表示されるモードに切り替えられることを確認してください（ch2 以降で使用）。

### 5. SQLite3

Kiro 版と共通です。

```bash
# macOS (プリインストール済みの場合あり)
sqlite3 --version

# Windows
winget install -e --id SQLite.SQLite
```

```bash
sqlite3 ":memory:" "CREATE TABLE test(id INTEGER, name TEXT); INSERT INTO test VALUES(1, 'hello'); SELECT * FROM test;"
# 1|hello と表示されればOK
```

### 6. spec-kit（ch1 で必要）

ch1 では GitHub 製の spec-kit を Claude Code に組み込み、Spec 駆動開発（Requirements → Design → Tasks → Implement）を行います。

セットアップは ch1 ディレクトリ内で実行します（ch1 開始時の手順として README にも記載）。

```bash
cd ch1
uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai claude
```

`.specify/` と `.claude/commands/` 配下に `/specify` `/plan` `/tasks` `/implement` などのスラッシュコマンドが追加されます。

### 7. playwright-cli（ch3-playwright で必要）

Node.js インストール後に以下を実行します。

```bash
npm install -g @playwright/cli@0.1.1
```

ブラウザバイナリをインストールします。

```bash
npx playwright install
```

動画録画機能を使う場合は、ffmpeg も追加でインストールします。

```bash
npx playwright install ffmpeg
```

動作確認します。

```bash
npx playwright-cli --version
```

各チャプターの起動方法は [README.md](./README.md) のチャプター構成を参照してください。
