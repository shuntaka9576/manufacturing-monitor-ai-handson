# ch1: 仕様駆動開発 - プロジェクト基盤 & DB

## 概要

製造設備モニタリングダッシュボードのデータ基盤を構築します。

Excelファイル（`sample_data.xlsx`）が用意されています。こちらを解析して、

- テーブルを作成する `schema.sql`
  - 設備マスタ
  - センサー時系列データ
  - ステータス変更履歴
- テーブルへ投入するスクリプト `seed.py`

## 体験すること（約10分｜経過 約10分）

Claude Code に **[spec-kit](https://github.com/github/spec-kit)** を組み込み、製造設備モニタリングダッシュボードのデータ基盤を構築します。`@sample_data.xlsx` を入力に、constitution で AI の過剰生成を縛ったうえで spec → plan → tasks → implement と段階的に詰めていきます（詳細フローは [§1 冒頭の図](#1-仕様駆動開発で-seedpy-を作る約40分経過-約40分) を参照）。

## 学ぶこと

### 概要

**仕様駆動開発（SDD: Spec-Driven Development）** は、コードを書き始める前に「何を / なぜ / どう作るか」を文書として固め、それを単一の真実として実装まで通すアプローチ。AI コーディングと組み合わせる文脈では、`spec.md / plan.md / tasks.md` のような構造化ドキュメントを生成・更新しながら段階的に詰めていく流れが定型になりつつある。

代表的な実装としては次のようなものがある。

- **[spec-kit](https://github.com/github/spec-kit)** — GitHub 公式の SDD フレームワーク。スラッシュコマンド (`/speckit-*`) で各工程を駆動する。本章で使用
- **[Kiro](https://kiro.dev/)** — AWS が提供する SDD 寄り IDE。spec / steering といった概念をエディタ自体に組み込んでいる
- **[cc-sdd](https://github.com/gotalab/cc-sdd)** — Claude Code / Codex / Cursor など複数エージェントに対応した SDD ハーネス

以下、本章では spec-kit を題材に SDD を実体験する。

### 仕様駆動開発の課題

- 工程が重くなる — Spec 作成・レビュー・コードとの同期で、開発リソースが大きく取られる
- 守られるとは限らない — LLM の出力は確率的で、Spec どおりの実装は保証されない。検証は結局人間が担う
- 変化に弱い — 要件→設計→実装の順序プロセスは、要件が流動的な案件と相性が悪い
- ドキュメントとして閉じない — spec.md / plan.md / tasks.md は「開発当時の意思決定スナップショット」として残るが、現行仕様を表す包括的ドキュメントにも、非開発者向け説明資料にもならない

```mermaid
graph LR
    A[Spec] --> B["Specレビュー(重い)"]
    B --> C[実装]
    C --> D["テスト/コードレビュー(人が主導)"]
    D --> E[フィードバック]

    style B fill:#fee,stroke:#c00,stroke-width:2px
    style D fill:#fee,stroke:#c00,stroke-width:2px
```

### 合意量で位置づけ、ハンズオンで体験する意味

合意量の観点で見ると、Zero-shot / Plan-Then-Execute / 仕様駆動開発 は どれだけ事前に合意してから実装するかの度合いが違うだけで、**直線上に並ぶ連続的な選択肢**だ。AI モデルが賢くなるほど、必要な合意量は減る方向に動く。

<!-- 画像生成プロンプト:
"Clean horizontal spectrum diagram. A single horizontal axis from left to right with three labeled positions:
- Left (around 10%): 'Zero-shot' / subtitle '雑な指示 → AI が一発生成'
- Middle (around 50%): 'Plan-Then-Execute' / subtitle '計画 → 実装、対話で都度補正'
- Right (around 90%): '仕様駆動 (spec-kit)' / subtitle '仕様 → 設計 → タスクを固めてから実装'
Axis label below: '実装前の合意量: 少 → 多'.
Below the main axis, a smaller secondary arrow labeled 'AI モデルが賢くなるほど中庸点が左へシフト' pointing left.
Flat design, corporate muted palette (navy, teal, warm amber accent), 16:9, clean sans-serif, white background, no extraneous decoration."
-->

![合意量スペクトラム](images/agreement_spectrum.png)

このスペクトラム上のどこに合わせるかは、現場の性格で変わる。

- **準委任契約ベース・要件流動性の高い現場** — 要件変更のたびに Spec を固め直す運用はコストと釣り合わない。Plan-Then-Execute（人手でプランを吟味し、AI に実装を委ねるスタイル）で左寄りに位置取るのが自然
- **規制・監査を伴うドメイン（金融・医療・製造業の品質保証など）** — 仕様の根拠とトレーサビリティを文書で残す要請から、右寄りに位置取る。納品物は人間向けの仕様書で、`spec.md / plan.md / tasks.md`（AI 向け構造化入力）とは粒度が違う。ただし、spec-kit の出力を起点に AI で人間向けドラフトを生成する運用は十分あり得る

なお、同じ Plan-Then-Execute でも、計画を細かく詰めずに一度実装させ、出来たものを見て修正指示で詰めていくやり方の方が早いケースは多い。プロトタイプや小規模変更では、合意を固めるより試行サイクルを多く回す方がフィードバックを得やすく、結果的に短い時間で着地する。

自分が担当する案件・チーム・モデル世代において、**この直線のどのあたりが最前線（コストとリターンが釣り合う点）か**は、両端を知らないと見極められない。仕様駆動開発を一度実体験しておくことで、「ここまで合意を固める価値があるか／もっと軽くしてよいか」を肌感覚で判断できるようになる。加えて SDD 自体、次のような場面では今でも有効に機能する手法だ。

<!-- 画像生成プロンプト:
"Two-row conceptual comparison diagram showing how a framework normalizes user input before AI amplification.
Top row labeled 'Plan-Then-Execute (直接渡し)':
- Three different-sized arrows on the left (representing varied prompt quality from different users) all pointing into a stylized 'AI 増幅器' icon (megaphone/speaker shape).
- Output side shows three different-sized arrows of varying quality.
Bottom row labeled 'spec-kit (フレームワーク経由)':
- Same three different-sized input arrows pointing first into a 'Framework (spec / plan / tasks)' box (depicted as a structured sieve/filter).
- After the framework, three uniform-sized arrows enter the 'AI 増幅器' icon.
- Output side shows three uniform-sized output arrows.
Clean diagrammatic style, corporate muted palette (navy, teal, warm amber accent), 16:9, clean sans-serif, white background."
-->

- **複数チーム・オフショア・非同期コラボレーション** — 会話履歴や Slack ログに依存できない環境で、リポジトリに残る仕様が引き継ぎ資料として機能する
- **AI コーディング経験の浅いメンバーで構成されたチーム** — フレームワークが「次に何を決めるか」を強制してくれるので、ガードレールとして機能する

![フレームワークが入力を正規化してから AI に渡す](images/framework_filter.png)

そして spec-kit というフレームワーク自体にも、Plan-Then-Execute では得にくい次の利点がある。

- **進め方をフレームワークが引き受ける** — 要件 → 質問 → 設計 → タスク → 実装の順序が固定済み。「次に何を聞くか / どこまで決めるか / いつ実装に入るか」をユーザーが毎回設計しなくていいので、中身の判断に集中できる
- **プロンプトの骨格をコマンド側が持つ** — Plan-Then-Execute だと「何を / どの観点から / どの順序で聞くか」を毎回プロンプトに書き起こす必要がある。一方 spec-kit は `/speckit-*` 各コマンドにテンプレート・問いかけ・出力形式が内蔵されており、ざっくりした 1 段落の seed を渡すだけで済む。さらに生成物（spec / plan / tasks）はリポジトリに残るため、入力と経緯の両面が定型化される
- **抜け漏れが計画前に必ず出る** — `/speckit-clarify` が計画ステップの**前段に固定**されている。AI に「質問して」と頼めば質問は来るが、それは計画の補足。spec-kit では設計入力として組み込まれているので、AI が勝手に仮定して進める前に欠損を出させられる
- **ロングタームなタスクで効く** — spec / plan / tasks がリポジトリに残るため、複数セッション・複数担当にまたがる中〜長期の work で「会話履歴に依存しない引き継ぎ」ができる。次の人（または次の自分）が会話を遡らなくても再開できる

## 前提

- [SETUP.md](../SETUP.md) に従い、Claude Code / uv / SQLite3 をインストール済み
- Claude Code にログイン済み（`/login` 完了）

## 0. ch1 プロジェクトを開く

ターミナルで ch1 ディレクトリに移動し、以下の手順を順に実行します。

### 0.1. 依存インストール

`openpyxl` / `pandas` など Excel 解析・DB 投入に必要な依存を `.venv` にインストールします。

```bash
cd ch1
uv sync
```

### 0.2. Claude Code を起動

```bash
claude
```

## 1. 仕様駆動開発で seed.py を作る（約40分｜経過 約40分）

ch1 には spec-kit が事前に組み込まれています（`.specify/` と `.claude/skills/` がコミット済み）。`/help` で各 `/speckit-*` コマンドが見えれば OK です。

```mermaid
graph TD
    A["/speckit-constitution<br/>plan mode"] -->|原則を定義| A1[(".specify/memory/<br/>constitution.md")]
    A1 --> B["/speckit-specify<br/>plan mode"]
    B -->|WHAT / WHY| B1[("specs/NNN-*/spec.md")]
    B1 --> C["/speckit-clarify<br/>plan mode"]
    C -->|曖昧性を解消し更新| B1
    B1 --> D["/speckit-plan<br/>plan mode"]
    D -->|HOW / 技術設計| D1[("specs/NNN-*/plan.md")]
    D1 --> E["/speckit-tasks<br/>plan mode"]
    E -->|タスク分解| E1[("specs/NNN-*/tasks.md")]
    E1 --> F["/speckit-implement<br/>通常 / auto-accept"]
    F -->|実装| F1[("db/schema.sql<br/>db/seed.py 等")]

    style A fill:#eef,stroke:#33c,stroke-width:1px
    style B fill:#eef,stroke:#33c,stroke-width:1px
    style C fill:#eef,stroke:#33c,stroke-width:1px
    style D fill:#eef,stroke:#33c,stroke-width:1px
    style E fill:#eef,stroke:#33c,stroke-width:1px
    style F fill:#efe,stroke:#3a3,stroke-width:1px
```

### 1.1. Constitution: `/speckit-constitution` で AI に制約を課す

過剰な機能・抽象化を抑える原則を `.specify/memory/constitution.md` に書き出します。spec-kit は以降のステップでこの原則を参照し、AI の生成を縛ります。

**実行モード: plan モード**（`shift+tab` でプロンプト下部の表示を `plan mode on` に切り替え）。Claude が原則 draft を提示 → `ExitPlanMode` 承認後に `.specify/memory/constitution.md` へ書き込みます。以降 1.5 まで同じ運用です。

```text
/speckit-constitution
このプロジェクトの全機能・全変更で守る原則を定めます。AI に過剰な機能・抽象化を生成させないため、以下を厳守してください。

I. Simplicity First — 最小構成で動くことを最優先する。複数機能を 1 つに統合できるなら統合する。
II. Speed First — 1 ファイルで実装できるなら 1 ファイル。モジュール分割は反復後に必要性が明確になってからにする。
III. Anti-Abstraction — ラッパー / Repository / Manager / DTO / Factory などの抽象層を導入しない。標準ライブラリと素直な関数で書く。
IV. YAGNI — 仕様で要求されていない機能（拡張性・設定可能性・汎用性）は実装しない。
```

#### チェック項目

- [ ] `.specify/memory/constitution.md` に 4 原則が反映されていること

### 1.2. Requirements: `/speckit-specify` で要件定義

`/speckit-specify` は **WHAT（何を作るか）と WHY（なぜ作るか）** のみを記述するステップです。技術スタックやディレクトリ構成といった HOW は次の `/speckit-plan` に委ねます。ここでは詳細を書き込まず、ざっくりした 1 段落だけ渡します。曖昧な部分は次の `/speckit-clarify` で対話的に埋めるので、最初から完璧な文章を書こうとしなくて構いません。

**実行モード: plan モード**（Claude が spec の構成案を提示 → 承認後に `specs/NNN-*/spec.md` へ書き込み）。

```text
/speckit-specify
製造設備モニタリングダッシュボード用のデータ基盤を作りたい。@sample_data.xlsx を唯一のデータソースとして、設備マスタ・センサー時系列・ステータス変更履歴の 3 種を保持し、初期データを投入する seed スクリプトを生成する。技術スタックや DDL は /speckit-plan で決めるのでここでは含めない。

ただし、gitのフックは実行しないでください。
```

実行すると `specs/NNN-*/spec.md` が作成されます。内容をレビューしてください。`NEEDS CLARIFICATION` マーカーが残っていても問題ありません。次の `/speckit-clarify` で潰します。

> [!NOTE]
> spec-kit 公式ガイドでは `/speckit-specify` で「Do not focus on the tech stack at this point」とされています。WHAT/WHY と HOW を明確に分離するのが仕様駆動開発の肝です。

#### チェック項目

- [ ] `specs/*/spec.md` が作成されていること
- [ ] `spec.md` に **技術スタック節（Python / SQLite 等）が含まれていない**こと
- [ ] 設備マスタ・センサー時系列・ステータス変更履歴の3種データが扱われていること

### 1.3. Clarify: `/speckit-clarify` で曖昧性を解消（必須）

`/speckit-specify` を最小限の文章で済ませた分、ここで対話的に詳細を詰めます。`spec.md` の `NEEDS CLARIFICATION` や曖昧な箇所を Claude が質問形式で投げてくるので、回答すると spec.md が更新されます。`/speckit-plan` 前に通すことで手戻りを減らします。

**実行モード: plan モード**（質疑応答で回答を集めたうえで spec.md 更新案を提示 → 承認後に書き込み）。

```text
/speckit-clarify
```

質問が来たらざっくり自己判断で回答してください。(今回のケースでは大枠前項でクリアされているため)

#### チェック項目

- [ ] `spec.md` の `NEEDS CLARIFICATION` が概ね解消されていること
- [ ] 「Excel を唯一のデータソースとし、ハードコードを排する」という非機能要件が反映されていること
- [ ] 冪等性・検証手順が記述されていること

### 1.4. Design: `/speckit-plan` で技術設計

ここから HOW を指示します。`/speckit-specify` から外した技術スタック・配置・DDL 設計をまとめて渡します。

**実行モード: plan モード**（アーキテクチャ・スキーマ案を提示 → 承認後に `specs/*/plan.md` へ書き込み）。

```text
/speckit-plan
技術スタックは Python 3.12 / SQLite / openpyxl を使用してください。

## ディレクトリ構成

- data/factory.db （生成物。.gitignore 対象）
- db/schema.sql （DDL）
- db/seed.py （Excel 読み込み + INSERT）
- db/connection.py （接続ヘルパー）

## DBスキーマ

CREATE TABLE は `@sample_data.xlsx` のカラム・型に準拠して設計してください。equipment / sensor_readings / status_logs の3テーブルと、(equipment_id, timestamp) の複合インデックスを作成します。

## 動作確認

`uv sync && uv run python db/seed.py` で投入できる状態にしてください。
```

`specs/*/plan.md` が生成されます。

#### チェック項目

- [ ] アーキテクチャ図・モジュール分割・処理フローが妥当か確認
- [ ] CREATE TABLE 文が `@sample_data.xlsx` のシート仕様と整合していること
- [ ] `data/factory.db` / `db/schema.sql` / `db/seed.py` / `db/connection.py` の生成計画が含まれていること

### 1.5. Tasks: `/speckit-tasks` でタスク分解

**実行モード: plan モード**（タスク分解案を提示 → 承認後に `specs/*/tasks.md` へ書き込み）。

```text
/speckit-tasks
```

`specs/*/tasks.md` が生成され、実装タスクに分解されます。

### 1.6. Implement: `/speckit-implement` で実装

**実行モード: plan モードを解除して通常モード**（`shift+tab` で `plan mode on` 表示を消した状態）。`/speckit-implement` は `tasks.md` を上から順に実行し、ファイル書き込み・コマンド実行が連続するため、plan モードでは毎タスクで承認待ちが発生します。承認の手間を更に減らしたい場合は、もう一度 `shift+tab` を押して **auto-accept モード**（プロンプト下部の表示が `auto-accept edits on`）にしてください。

タスク実行のクレジット消費を抑えるため、ここでモデルを Sonnet に切り替えます。

```text
/model sonnet
/speckit-implement
```

> [!NOTE]
> spec-kit の `/speckit-implement` は `tasks.md` を上から順に実装していきます。タスクが複数に分かれている場合、「次のタスクに進んでください」と指示すれば続行します。

## 2. 検証（約10分｜経過 約50分）

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

## 3. 時間が余ったら

### 3.1. テストケースを精査する

AIが生成したテストは冗長になりがちです。生成された `tests/` 以下を眺めて、以下のような観点で冗長部分を探してみてください。

- hypothesis などのプロパティベーステストを、固定Excelに対して使っていないか
- schema.sql の文字列をパースするテストで、DDL実行＋テーブル存在チェックで代替できないか
- 1,152行のセンサーデータを全行比較していないか（件数＋数行サンプルで十分）

### 3.2. 稼働分析SQLをAIに生成させる

```text
各設備について、ステータスごとの滞在時間（分）を計算したSQLを作成し、実行できることを確認したのち提供してください
```

```text
各設備のセンサーデータについて、直近6件の移動平均温度を計算し、現在値が移動平均の1.5倍を超えるレコードを異常候補として抽出してください
```

生成されたSQLを `sqlite3 data/factory.db` で実行し、結果を確認してみてください。
