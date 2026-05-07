# ch3-skill-creator: Agent Skills - skill-creator によるスキル開発

## 概要

ch2 で構築した設備ダッシュボードをそのまま題材に、Agent Skills の以下の流れを 4 つの Phase で体験します。

- Phase 1: skill-creator を導入する ── Claude Code 公式マーケットプレイスからインストール
- Phase 2: 自作スキルを作って育てる ── 「事前調査 → 初版 → Progressive Disclosure 改善 → 対話化」のサイクル
- Phase 3: 外部スキルを扱う ── 公式マケプレ外のスキルを `gh skill` で導入
- Phase 4: まとめ

### Agent Skills とは

Agent Skills は、AI エージェントに新しい能力を追加するためのポータブルな命令パッケージです（[agentskills.io](https://agentskills.io) 標準）。Claude Code では `.claude/skills/<name>/SKILL.md` を配置するだけで、コンテキストに応じて自動的にスキルが活性化します。

1. Discovery（発見）: 起動時にスキル名と説明のみを読み込む（〜100 語/skill）
2. Activation（活性化）: リクエストがスキルの説明にマッチすると、本文全体を読み込む
3. Execution（実行）: `scripts/` や `references/` を必要に応じて読み込む

本章では `skill-creator` を使って設備稼働日報を出力する自作スキル（daily-operations-report）を作成し、Progressive Disclosure（Level 1/2/3）を意識したレビューサイクルで改善します。

### 前提

- ch2 で作成した設備ダッシュボード（`app.py`, `pages/01_equipment_dashboard.py`）が存在する
- Claude Code がインストール済み
- （Phase 3 用）GitHub CLI v2.90.0+。導入方法は [SETUP.md](../SETUP.md) §9 を参照

---

## Phase 1: skill-creator を導入する（約8分｜経過 約8分）

Anthropic 公式の [`anthropics/skills`](https://github.com/anthropics/skills) リポジトリは Claude Code のプラグインマーケットプレイスとして登録できます。`/plugin marketplace add` と `/plugin install` のスラッシュコマンドだけで `skill-creator` を導入します。追加ツールは不要です。

### 1.1. 環境セットアップ（約3分）

#### 章ディレクトリに移動

この章は専用の Python 設定を持ちます。必ず章ディレクトリを開いた状態で作業してください。

```bash
cd ch3-skill-creator
```

#### Streamlit アプリケーションの起動（ch2 完成状態の確認）

```bash
uv sync
uv run python db/seed.py
uv run streamlit run app.py
```

`http://localhost:8501` でダッシュボードが表示されることを確認してください（ch2 と同じ内容）。

### 1.2. 公式マーケットプレイスを追加（約2分）

Claude Code を起動します。

```bash
claude
```

Anthropic 公式の `anthropics/skills` を marketplace として登録します。

```text
/plugin marketplace add anthropics/skills
```

登録されたことを確認します。

```text
/plugin marketplace list
```

`anthropic-agent-skills` が表示されれば成功です。

> [!NOTE]
> バージョンを固定したい場合は `anthropics/skills#v1.0.0` のようにタグ指定でマーケットプレイスを追加してください。

### 1.3. skill-creator をインストール（約2分）

```text
/plugin install example-skills@anthropic-agent-skills
```

インストールスコープを聞かれたら Project（`.claude/settings.json` に記録）を選ぶと、チームで共有できる形になります。

### 1.4. 認識確認（約1分）

```text
/plugin list
```

`skill-creator@anthropic-agent-skills` が enabled の状態で表示されていればOKです。`/` を入力して補完候補に `skill-creator` が現れることも確認してください。

#### チェック項目

- [ ] `/plugin marketplace list` に `anthropic-agent-skills` が登録されていること
- [ ] `/plugin list` で `skill-creator@anthropic-agent-skills` が enabled であること
- [ ] `/` 補完に `skill-creator` が表示されること

---

## Phase 2: 自作スキルを作って育てる（約41分｜経過 約49分）

「作る → 出す → 直す → 対話化」のサイクルでスキルを育てます。先に Phase 2.1 で必要な仕様知識を仕入れてから、Phase 2.2 以降の実装に入ります。

### 2.1. 事前調査（約7分）

後の Phase で使う知識を、メインセッションを汚さずに先に揃えておきます。

#### claude-code-guide で Agent Skills の仕様を調べる（約4分）

Claude Code 組み込みサブエージェントの `claude-code-guide` を呼んで、後で使う仕様をまとめて調べさせます。

```text
claude-code-guide を使って、SKILL.md の YAML frontmatter で指定できる項目と、
AskUserQuestion ツールの使い方（引数構造と典型的な使いどころ）を教えてください。
```

#### AskUserQuestion を直接体験する（約3分）

調べた `AskUserQuestion` を、まずメインセッションから直接呼ばせて UI を体感します。Phase 2.4 でスキルに組み込ませる前に「どんな UI なのか / どう返却されるのか」を手で触るのが目的です。

Claude Code に以下を入力します。

```text
AskUserQuestion を使って、私に次の 3 問を一度に聞いてください。

1. このあと作る daily-operations-report スキルの出力先ディレクトリはどこが良いですか？
   選択肢: reports/, output/, docs/reports/
2. 日報のフォーマットはどれが好みですか？
   選択肢: Markdown のみ, Markdown + CSV, Markdown + HTML
3. 異常停止の検知閾値は固定値で良いですか？
   選択肢: 固定値でOK, 設定ファイルで外出し, AI に推定させる

回答をもらったら、「了解しました。この設定でスキル作成フェーズに進みます」とだけ返してください。
```

- Claude Code のチャット下部に選択肢 UI（チップ or ラジオボタン）が表示されます
- 自由入力欄（"Other"）も自動で提供されるため、選択肢に無い答えも入れられます
- Phase 2.4 で skill-creator に組み込ませる動作が、今ここで手触りとして分かるのがこのステップの狙いです

> [!NOTE]
> ここで選んだ回答は後続の Phase には使いません。Phase 2.2 では意図的に「最小の情報だけ」で skill-creator に初版を作らせます。AskUserQuestion の UI を触ること自体が目的です。

#### チェック項目

- [ ] チャット欄に選択肢 UI が表示されること
- [ ] 3 問まとめて聞かれる（`questions` 配列に 3 要素が入った場合の挙動）
- [ ] 選択後、Claude Code が簡潔に了解の返事をするだけで余計な実装には進まないこと

### 2.2. 初版を作る（約11分）

> [!NOTE]
> Phase 2.1 で `claude-code-guide` から得た frontmatter の知識を、ここで実際のスキル作成に活かします。

ch2 の SQLite DB（`data/factory.db`）を題材に、指定日 24 時間分の設備稼働レポートを Markdown で出力するスキルを作ります。

> [!NOTE]
> seed データ（`sample_data.xlsx`）は 2026-03-01 〜 2026-03-08 の固定期間なので、本章では対象日を 2026-03-07 に固定します。実運用スキルでは「昨日」を既定にしつつ、任意の対象日を引数で受けられるよう設計するのが良いでしょう。

#### skill-creator に依頼（約8分）

Claude Code で以下を入力します。

```text
/skill-creator を使って、以下の要件のスキルを作成してください。

- スキル名: daily-operations-report
- 目的: data/factory.db から指定日 24 時間分の設備稼働データを集計し、日報を Markdown で出力する（既定の対象日は 2026-03-07、任意日を引数で受け取れる設計）
- 集計内容:
  - 設備別の稼働時間 / 停止時間 / 異常停止件数
  - 期間中の総生産数
  - 主要センサー値（temperature, vibration など）の平均/最大
- 出力: `reports/YYYY-MM-DD-operations.md` に保存
- 実装先: .claude/skills/daily-operations-report/ 配下
```

skill-creator が対話でヒアリングしてきたら、あえて最小限の情報だけ答えて先に進めます（わざと粗い初版を作るため）。

#### 生成されたスキルを確認

```bash
ls .claude/skills/daily-operations-report/
cat .claude/skills/daily-operations-report/SKILL.md
```

#### 初版で日報を出力する（約3分）

Claude Code で以下を入力します。

```text
2026-03-07 の稼働日報を出力してください
```

`daily-operations-report` スキルが自動でトリガーされ、`reports/2026-03-07-operations.md` が生成されます。

#### チェック項目

- [ ] `.claude/skills/daily-operations-report/SKILL.md` が存在すること
- [ ] description が曖昧、SQL/Python が SKILL.md 本文に直書き、scripts 未分離 ── といった「太った初版」になっていること（Phase 2.3 のレビューで改善します）
- [ ] 指定ディレクトリに日報 `.md` が生成されていること
- [ ] 設備別の稼働率・停止件数・生産数が含まれていること

### 2.3. Progressive Disclosure で改善する（約14分）

Agent Skills は 3 つの Level で遅延ロードされる設計です（Progressive Disclosure）。

- Level 1 / Metadata（name + description）— 起動時に全スキル分が system prompt に常駐。〜100 語/skill に抑える
- Level 2 / SKILL.md 本文 — trigger 時のみ全文ロード。500 行未満が推奨
- Level 3 / Bundled Resources（`scripts/`, `references/`, `assets/`） — 本文から参照された時だけ読込。scripts は実行のみで context を食わない

重い情報を Level 3 に退避するのが鉄則です。skill-creator にレビューを依頼します。

> [!NOTE]
> なぜ skill-creator は初版で綺麗に作ってくれないのか（マッチポンプ疑惑）
>
> 「新規生成の時点で Progressive Disclosure を満たしてくれればレビュー不要では？」は正当な疑問です。しかし、この 2 パス構造は skill-creator の限界ではなく、情報が生成行為によってしか現れない問題に対する合理的設計と見るのが正確です。
>
> 1. 初版作成時には配置判断の根拠が存在しない — 「何が重くて何を分離すべきか」を決めたくても、SQL の具体形も SKILL.md 本文の量もまだ存在しない。分離点を決める材料がない。
> 2. 生成した成果物そのものが、次パスの入力コンテキストになる — 一度作って実体（Level 2 の膨らみ方、scripts に出せる純粋コード、references に出せる仕様情報）を手に入れて、はじめて最適配置を判断できる。
> 3. ソフトウェア設計で見慣れたパターン — Spike → Refactor / 下書き → 推敲 / Actor-Critic / Reflection loops。いずれも「作ってみないと構造が決まらない問題」を 2 パスで解く手法。
> 4. 教育的デザインとしても意図的 — Phase 2.2 で「わざと粗い初版を作る」と明示しており、差分（初版 → 改善版）を体験させることが狙い。
>
> 実運用でも「生成 → 実測 → 構造化」のサイクルは有効です。AI が作るスキルも、生成したものを実測して構造を整える工程があってはじめて筋の通った資産になる、という学びを持ち帰ってください。

#### レビュー依頼

> [!IMPORTANT]
> ここは Plan モードで実行してください。Claude Code のプロンプト下部が `auto mode on` や `accept edits on` になっている場合は、`Shift+Tab` を押して `plan mode on` に切り替えます。Plan モードでは skill-creator が提案プランのみを出力し、ファイル変更は行いません。受講者が何を指摘してきたかを吟味してから適用するのがこのフェーズの学びです。

```text
/skill-creator で .claude/skills/daily-operations-report/ をレビューして、気になった点を改善してください。
```

観点を人間側から指示する必要はありません。Progressive Disclosure の評価は skill-creator 自身が持つべき知識です。skill-creator が差分を提案してきたら、どのレベルの問題をどう指摘してきたかに注目しつつ適用してください（Plan を承認すると自動で通常モードに戻り、実装が走ります）。

#### 改善後の構造を確認

期待される構成例:

```
.claude/skills/daily-operations-report/
├── SKILL.md                      # Level 2: 高レベルガイド (短く保つ)
├── references/
│   └── schema.md                 # Level 3: DB スキーマ・SQL サンプル
├── scripts/
│   └── aggregate.py              # Level 3: 集計ロジック本体
└── assets/
    └── report-template.md        # Level 3: 出力テンプレート
```

#### チェック項目

- [ ] description が「日報を出力したいときに使う」と明確に伝わる記述になっていること
- [ ] SKILL.md 本文が大幅に短くなっていること
- [ ] `scripts/aggregate.py` が分離されていること
- [ ] `references/` または `assets/` に詳細が退避されていること

### 2.4. AskUserQuestion で対話化する（約6分）

ここまでで Progressive Disclosure の構造は整いました。最後に「最小の指示で動くスキル」から「実運用で任せられる対話型スキル」へ進化させます。

`AskUserQuestion` は選択肢を明示して対話するツールです。自由入力よりモデルの暴走を抑え再現性が上がるため、運用フローに組み込みたいスキルでは第一選択になります。

Phase 2.1 で調べた引数構造を頭に置きつつ、skill-creator にリファクタを依頼します。

> [!IMPORTANT]
> このフェーズも Plan モードで実行してください（`Shift+Tab` で `plan mode on`）。

```text
/skill-creator で .claude/skills/daily-operations-report/ に AskUserQuestion を使った
対話確認を追加してください。以下の2シナリオで使います。

1. 対象日の指定が無い場合: seed データが存在する期間（2026-03-01 〜 2026-03-08）から選ばせる
2. 同じ日付のレポートが既に reports/ にある場合: 「上書き / 別名で保存 / 中断」の3択を出す
```

skill-creator が差分を提案するので、内容を確認して適用します。

#### 動作確認: 対象日を省略したプロンプト

```text
昨日の稼働日報を出力してください
```

対象日の選択肢 UI が出ることを確認してください（2026-03-01 〜 2026-03-08 から選ばせる）。

#### 動作確認: 既存レポートと同じ日付を指定

```text
2026-03-07 の稼働日報を出力してください
```

（前のフェーズで既に `reports/2026-03-07-operations.md` が存在している前提）上書き / 別名で保存 / 中断 の3択 UI が出ることを確認してください。

#### 動作確認: 改善版で最終形

```text
2026-03-08 の稼働日報を出力してください
```

新しい日付で実行し、Progressive Disclosure の構造 × AskUserQuestion の対話確認が合わさった実運用寄りのスキルになっていることを確認します。

#### チェック項目

- [ ] `SKILL.md` または `scripts/` に `AskUserQuestion` の呼び出しが記述されていること
- [ ] 対象日を省略すると 2026-03-01 〜 2026-03-08 の選択肢 UI が出ること
- [ ] 既存日付を指定したときに上書き確認ダイアログが出ること

### 2.5. Phase 2 検証（約3分）

#### チェック項目

- [ ] `.claude/skills/daily-operations-report/` が存在すること
- [ ] 改善後の `daily-operations-report` が Progressive Disclosure の 3 レベルを活用した構造になっていること
- [ ] `daily-operations-report` に `AskUserQuestion` による対話確認が組み込まれていること
- [ ] `claude-code-guide` を使って仕様調査した経験があること（メインセッションとは別タスクで動くことを体感済み）

---

## Phase 3: 外部スキルを扱う（約5分｜経過 約54分）

Phase 1〜2 では Claude Code 公式マケプレにあるスキルの扱いを学びました。実務では GitHub の他リポジトリで公開されているスキルや、社内独自スキルを扱いたい場面もあります。Phase 3 では代表的なツールとして `gh skill` を試します。

| ツール                   | 強み                                               | 向いているケース                               |
| ------------------------ | -------------------------------------------------- | ---------------------------------------------- |
| Claude Code 公式マケプレ | 公式登録済みスキルを `/plugin install` で一発導入  | Anthropic 公式配布を使うとき（推奨）           |
| `gh skill`               | GitHub CLI から `--pin <tag>` でバージョン固定導入 | 非公式 GitHub リポジトリのスキルを入れたいとき |

> [!NOTE]
> 事前に [SETUP.md §9](../SETUP.md) を見て GitHub CLI v2.90.0+ を用意してください。`gh skill` は Public Preview のため仕様変更の可能性があります。

### 3.1. インストールと一覧

別のスキル（例として公式リポジトリの `mcp-builder`）を pin 付きで入れる例です。

```bash
gh skill install anthropics/skills mcp-builder --agent claude-code --pin <タグ>
```

インストール済みスキルを一覧します。

```bash
gh skill list
```

### 3.2. 更新と削除

```bash
gh skill update --all
gh skill uninstall <owner>/<repo> <skill>
```

### チェック項目

- [ ] `gh skill list` にインストールしたスキルが表示されること
- [ ] Claude Code の `/` 補完に当該スキルが現れること

---

## Phase 4: まとめ

- 公式マケプレ（`/plugin install`）が第一選択。Anthropic 公式のスキルはこれで入る
- GitHub の任意リポジトリのスキルは `gh skill` で pin 導入
- スキルは「作る → 出す → 直す → 対話化」のサイクルで育てる。初版で完璧を狙わず、Progressive Disclosure を意識した 2 パス構造で改善する

どちらの導入方法を使っても最終的には `.claude/skills/<name>/SKILL.md` が配置され、Claude Code から同じ使い心地になります。配布元と管理粒度で使い分けてください。
