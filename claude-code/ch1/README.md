# ch1: Spec駆動開発 - プロジェクト基盤 & DB

## 概要

製造設備モニタリングダッシュボードのデータ基盤を構築します。

Excelファイル（`sample_data.xlsx`）が用意されています。こちらを解析して、

- テーブルを作成する `schema.sql`
  - 設備マスタ
  - センサー時系列データ
  - ステータス変更履歴
- テーブルへ投入するスクリプト `seed.py`

## 体験すること（約10分｜経過 約10分）

Claude Code に **[spec-kit](https://github.com/github/spec-kit)** を組み込み、Spec駆動ワークフロー（`/speckit.constitution` → `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`）で製造設備モニタリングダッシュボードのデータ基盤を構築します。Excel解析結果を `CLAUDE.md` などプロジェクト知識に登録してから Spec を生成する流れを体験します。

### Spec駆動開発とは

Spec駆動開発は、AIに対して構造化された仕様書を入力として与え、コードを生成させる開発手法です。自然言語プロンプトから即座にコードを生成するVibe Codingとは異なり、Requirements（要件定義）→ Design（設計）→ Tasks（タスク分解）の3ステップで進行します。成果物はバージョン管理されるMarkdownファイルとして永続化されます。

### Spec駆動開発の課題

Spec駆動開発にはいくつかの課題が指摘されています。

- 要件→設計→実装という順序的プロセスがウォーターフォールに似ており、ソフトウェア開発の非決定的な性質と相性が悪い
- 単純なバグ修正が4つのユーザーストーリー・16の受け入れ基準に膨張するなど、小さな変更に対して過剰になりやすい
- コードの進化に合わせて仕様を同期し続けるメンテナンスコストが増大する
- 包括的な仕様を与えても、AIエージェントが指示を誤解・無視するケースがある
- LLMの出力は確率的であり、Specどおりに実装される保証はない。正確性を検証する仕組みは未整備で、テストやコードレビューは人間が担わなければならない
- 既存の開発プロセスを変えずにSDDを導入した場合、Specレビューという重い工程が単純に1つ追加されるだけになる

```mermaid
graph LR
    A[Spec] --> B["Specレビュー(重い)"]
    B --> C[実装]
    C --> D["テスト/コードレビュー(人が主導)"]
    D --> E[フィードバック]

    style B fill:#fee,stroke:#c00,stroke-width:2px
    style D fill:#fee,stroke:#c00,stroke-width:2px
```

### それでもSpec駆動が重要な理由

SDDはウォーターフォールではなく、繰り返しを前提としたループ構造です。AIが実装→テスト→フィードバックのサイクルを高速化することで、日単位での反復が可能になります。

```mermaid
graph LR
    A[Spec作成<br/>AI+人間] --> B[レビュー/承認<br/>承認ゲート]
    B --> C[実装<br/>AI]
    C --> D[テスト/メトリクス検証<br/>AI]
    D --> E[フィードバック<br/>人間]
    E -->|Specを更新| A
    C <-->|AIにより高速化| D
```

- 検証可能性: Specの振る舞い仕様がユニットテストと結びつくことで、Specから下流の検証まで自動化できる
- フィードバックループ: Specは一度きりではなく、仮説と要件を一時的にFixした反復プロセス。短いサイクルでSpec自体を洗練させる

## 前提

- [SETUP.md](../SETUP.md) に従い、Claude Code / uv / SQLite3 をインストール済み
- Claude Code にログイン済み（`/login` 完了）

## 0. ch1 プロジェクトを開く

ターミナルで ch1 ディレクトリに移動し、Claude Code を起動します。

```bash
cd ch1
claude
```

## 1. Excelの内容を解析して知識に登録する（約10分｜経過 約10分）

### 1.1. エクセル解析プロンプトを入力

以下のプロンプトを入力します。`@sample_data.xlsx` でファイルを添付してください。

```text
@sample_data.xlsx を添付します。

以下の観点で構造を分析してください。

1. シート一覧と各シートの役割
2. 各シートのカラム構成（列名・データ型・サンプル値）
3. シート間の関連性（IDの参照関係など）
4. データの件数や値の傾向

結果はシートごとにまとめてください。
```

#### チェック項目

- [ ] エクセルシートと比較して、ざっくりあっていることを確認してください

### 1.2. 解析結果を永続化する

続けて以下を入力し、解析結果を `CLAUDE.md` に書き出してプロジェクト知識として永続化します（Kiro の Steering 相当）。

```text
上記の解析結果を CLAUDE.md にプロジェクト知識として追記してください。
「## sample_data.xlsx のシート仕様」という見出しで、シート構成・カラム情報・データ件数を記述してください。
```

> [!NOTE]
> `CLAUDE.md` は Claude Code が自動的に読み込むプロジェクト知識ファイルです。セッションをまたいでも内容が保持され、以降のプロンプトで常に参照されます。

#### チェック項目

- [ ] `CLAUDE.md` が作成（または追記）されていることを確認してください
- [ ] `sample_data.xlsx` を開き、シート構成・カラム情報・データ件数が CLAUDE.md の内容と一致していることを確認してください

## 2. spec-kit で seed.py の仕様を作成する（約30分｜経過 約50分）

### 2.1. spec-kit を導入する

Claude Code を一度終了し、ch1 ディレクトリで spec-kit を初期化します。バージョンは `v0.8.5` で固定し、ハンズオン中の挙動を揃えます。

```bash
uvx --from git+https://github.com/github/spec-kit.git@v0.8.5 specify init --here --integration claude
```

`.specify/` と `.claude/commands/` 配下に `/speckit.constitution` `/speckit.specify` `/speckit.clarify` `/speckit.plan` `/speckit.tasks` `/speckit.implement` などのスラッシュコマンドが追加されます。

> [!NOTE]
> エージェント指定は現行の `--integration claude` を使います。旧 `--ai claude` は deprecated で v0.10.0 以降は廃止予定です。

```bash
claude
```

Claude Code を再起動し、`/help` でコマンド一覧に `/speckit.specify` が現れていれば OK です。

### 2.2. Constitution: `/speckit.constitution` でプロジェクト原則を定義

`/speckit.specify` の前に、プロジェクト全体で守りたい原則を `.specify/memory/constitution.md` に書き出します。spec-kit が以降のステップでこのファイルを参照し、原則からの逸脱を抑制します。

```text
/speckit.constitution
このプロジェクトは Spec 駆動開発のハンズオン教材です。以下の原則を守ってください。

- ハードコードされたデータ定数を持ち込まない。データソースは Excel (sample_data.xlsx) のみ。
- スキーマや仕様の根拠は CLAUDE.md「sample_data.xlsx のシート仕様」に従う。
- spec は WHAT/WHY、plan は HOW、と役割を分ける。
- 投入後の検証手順を必ず添える。
```

#### チェック項目

- [ ] `.specify/memory/constitution.md` が作成され、原則が反映されていること

### 2.3. Requirements: `/speckit.specify` で要件定義

`/speckit.specify` は **WHAT（何を作るか）と WHY（なぜ作るか）** のみを記述するステップです。技術スタックやディレクトリ構成といった HOW は次の `/speckit.plan` に委ねます。

```text
/speckit.specify
製造設備の稼働状況をリアルタイムで監視するダッシュボードアプリのデータ基盤を作ります。
sample_data.xlsx を唯一のデータソースとして、初期データを投入する seed スクリプトを生成したい。

## 背景・目的

- 工場の設備マスタ・センサー時系列・ステータス変更履歴を一元的に保持し、後続のダッシュボードから参照できる状態にする
- マスタや時系列データはすべて Excel から取り込む。スクリプト内にデータ定数をハードコードしない（運用で Excel を差し替えれば再投入できる状態にする）

## 扱うデータ

Excel のシート構成・カラム・件数の詳細は CLAUDE.md「sample_data.xlsx のシート仕様」を参照してください。

- 設備マスタ
- センサー時系列データ
- ステータス変更履歴

## 受け入れ条件（WHAT）

- 3 種のテーブルに Excel の全件が投入されること
- 設備マスタの現在ステータスが、ステータス変更履歴の最新エントリと整合すること
- スクリプトを再実行してもデータが破損せず初期状態を再現できること
- 投入結果を確認するための検証手順が定義されていること

技術スタック・ディレクトリ構成・DDL の詳細はこの段階では決めず、/speckit.plan で扱います。
```

実行すると `specs/NNN-*/spec.md` が作成されます。内容をレビューしてください。

> [!NOTE]
> spec-kit 公式ガイドでは `/speckit.specify` で「Do not focus on the tech stack at this point」とされています。WHAT/WHY と HOW を明確に分離するのが Spec 駆動の肝です。

#### チェック項目

- [ ] `specs/*/spec.md` が作成されていること
- [ ] `spec.md` に **技術スタック節（Python / SQLite 等）が含まれていない**こと
- [ ] 「Excel を唯一のデータソースとし、ハードコードを排する」という非機能要件が反映されていること
- [ ] 設備マスタ・センサー時系列・ステータス変更履歴の3種データが扱われていること

### 2.4. Clarify: `/speckit.clarify` で曖昧性を解消（任意）

時間に余裕があれば実行します。`spec.md` の `NEEDS CLARIFICATION` を質問形式で対話的に埋め、`/speckit.plan` 時の手戻りを減らせます。

```text
/speckit.clarify
```

> [!TIP]
> 受講中はスキップしても先に進めますが、本番開発では `/speckit.plan` の前に通すのが推奨フローです。

### 2.5. Design: `/speckit.plan` で技術設計

ここから HOW を指示します。`/speckit.specify` から外した技術スタック・配置・DDL 設計をまとめて渡します。

```text
/speckit.plan
技術スタックは Python 3.12 / SQLite / openpyxl を使用してください。

## ディレクトリ構成

- data/factory.db （生成物。.gitignore 対象）
- db/schema.sql （DDL）
- db/seed.py （Excel 読み込み + INSERT）
- db/connection.py （接続ヘルパー）

## DBスキーマ

CREATE TABLE は CLAUDE.md「sample_data.xlsx のシート仕様」のカラム・型に準拠して設計してください。equipment / sensor_readings / status_logs の3テーブルと、(equipment_id, timestamp) の複合インデックスを作成します。

## 動作確認

`uv sync && uv run python db/seed.py` で投入できる状態にしてください。
```

`specs/*/plan.md` が生成されます。

#### チェック項目

- [ ] アーキテクチャ図・モジュール分割・処理フローが妥当か確認
- [ ] CREATE TABLE 文が CLAUDE.md のシート仕様と整合していること
- [ ] `data/factory.db` / `db/schema.sql` / `db/seed.py` / `db/connection.py` の生成計画が含まれていること

### 2.6. Tasks: `/speckit.tasks` でタスク分解

```text
/speckit.tasks
```

`specs/*/tasks.md` が生成され、実装タスクに分解されます。

### 2.7. Implement: `/speckit.implement` で実装

タスク実行のクレジット消費を抑えるため、ここでモデルを Sonnet に切り替えます。

```text
/model sonnet
/speckit.implement
```

> [!NOTE]
> spec-kit の `/speckit.implement` は `tasks.md` を上から順に実装していきます。タスクが複数に分かれている場合、「次のタスクに進んでください」と指示すれば続行します。

## 3. 検証（約10分｜経過 約60分）

Claude Code を終了し、ターミナルで検証します。

```bash
# 依存インストール & シード実行
uv sync
uv run python db/seed.py

# テスト実行（生成されていれば）
uv run pytest -v
```

sqlite3 CLIでデータを確認します。

```bash
sqlite3 data/factory.db
```

```sql
.tables
.schema equipment

SELECT COUNT(*) FROM equipment;
SELECT COUNT(*) FROM status_logs;
SELECT COUNT(*) FROM sensor_readings;

SELECT * FROM equipment;
SELECT * FROM sensor_readings WHERE equipment_id = 1 LIMIT 5;

PRAGMA foreign_key_list(status_logs);

.quit
```

> [!NOTE]
> AIの出力により、DBファイルのパスやテーブル名が異なる場合があります。実際に生成されたコードに合わせて読み替えてください。

## 4. 時間が余ったら

### 4.1. テストケースを精査する

AIが生成したテストは冗長になりがちです。生成された `tests/` 以下を眺めて、以下のような観点で冗長部分を探してみてください。

- hypothesis などのプロパティベーステストを、固定Excelに対して使っていないか
- schema.sql の文字列をパースするテストで、DDL実行＋テーブル存在チェックで代替できないか
- 1,152行のセンサーデータを全行比較していないか（件数＋数行サンプルで十分）

### 4.2. 稼働分析SQLをAIに生成させる

```text
各設備について、ステータスごとの滞在時間（分）を計算したSQLを作成し、実行できることを確認したのち提供してください
```

```text
各設備のセンサーデータについて、直近6件の移動平均温度を計算し、現在値が移動平均の1.5倍を超えるレコードを異常候補として抽出してください
```

生成されたSQLを `sqlite3 data/factory.db` で実行し、結果を確認してみてください。
