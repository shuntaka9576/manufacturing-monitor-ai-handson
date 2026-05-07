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

`AskUserQuestion` をスキルに組み込めると、**AI に独断させたくない判断ポイント**（対象日が無い / 既存ファイルと衝突する など）で、確定した選択肢から人間に決めさせる**安全な分岐**をスキル内に作れます。これが無いスキルは「自由入力 → AI が勝手に解釈 → 意図しない上書き」を起こしがちです。

Phase 2.4 で daily-operations-report にこの分岐を組み込みますが、その前に素のツールを 1 度呼んで挙動を確認します。AskUserQuestion には**単一選択 / 複数選択 / preview 付き比較 / 推奨ラベル**といった機能差があるため、3 問それぞれで別の機能を試して引き出しを増やします。

Claude Code に以下を入力します。

```text
AskUserQuestion を使って、以下の 3 問を一度に聞いてください。
それぞれ異なる機能を試したいので、必ず指定の構成にしてください。

1.【単一選択 + 各選択肢に description】
   質問: 日報の出力先ディレクトリはどこが良いですか？
   選択肢: reports/, output/, docs/reports/
   各選択肢に「なぜそれが向くか」の description を 1 行ずつ付けてください。

2.【複数選択 (multiSelect: true)】
   質問: 日報に含めたい補足セクションをすべて選んでください。
   選択肢: 異常停止サマリ, センサー値推移, 担当者シフト集計, 翌日の予定

3.【preview 付き + Recommended ラベル】
   質問: SKILL.md frontmatter のサンプルとしてどれを採用しますか？
   選択肢を 3 つ用意し、それぞれ preview に YAML スニペット (4〜6 行) を入れてください。
   推奨案を先頭に置き、ラベル末尾に "(Recommended)" を付けてください。

回答をもらったら「了解しました」とだけ返してください。
```

回答内容は使いません。3 問それぞれで UI が違うこと（チップ単一選択 / チェックボックス複数選択 / 右側プレビューの side-by-side）を目で確認してください。

#### チェック項目

- [ ] 1 問目で各選択肢に description が表示されること
- [ ] 2 問目で複数選択できる UI（チェックボックス相当）になっていること
- [ ] 3 問目で選択肢を切り替えると右側 / 下に YAML プレビューが出ること（先頭に "(Recommended)" 付き）

### 2.2. 初版を作る（約11分）

ch2 の SQLite DB（`data/factory.db`）を題材に、指定日 24 時間分の設備稼働レポートを Markdown で出力するスキルを作ります。seed データの期間は 2026-03-01 〜 2026-03-08 なので、対象日は 2026-03-07 に固定します。

#### skill-creator に依頼（約8分）

skill-creator は以下のような流れでスキルを育てる前提で作られています。中央の **評価ループ** が肝で、テスト実行 → 評価（定量＋定性）→ 改善を回し続けることで、初版で粗かったスキルが実運用に耐える品質に上がります。Phase 2.2 以降を進めるときはこのメンタルモデルを意識してください。

![skill-creator のフロー: 意図をつかむ → ヒアリング・調査 → SKILL.md を下書き → 評価ループ（テスト実行 → 評価 → 改善）→ 説明を最適化](./images/skill-creator-flow.png)

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

次のフェーズに進む

> AI: 次のステップとして、テストケースを作って評価ループを回すこともできますが、どうしますか？

```text
お願いします。
```

skill-creator はここから **LLM as a Judge** という方式で評価を回します。テストプロンプトをスキル付き Claude に投げて出力を集め、それを別の LLM（Judge）が `expected_output` と照合してスコアと指摘を返します。Judge 自身も LLM なので自然文の出力でも採点でき、その結果が SKILL.md 改善のインプットになるのが肝です。

![LLM as a Judge: evals.json のテストケースをスキル実行に投げ、出力を別の LLM Judge が rubric と照合してスコア + フィードバックを返し、SKILL.md 改善ループに戻る](./images/llm-as-a-judge.png)

#### eval-viewer で結果を確認する

skill-creator は `eval-viewer/generate_review.py` を実行し、評価結果をブラウザで確認できる HTML を出力します。Outputs タブで、各テストケースのプロンプトと、スキル付き Claude が生成した日報本文を並べて確認できます。

![eval-viewer Outputs タブ: プロンプトと、スキル付き Claude が生成した Markdown 日報の出力本文が表示される](./images/eval-viewer-output.png)

下部にはアサーション一覧があり、Judge が rubric 各項目（必須セクションの有無、日付一致など）を ✓/✗ で自動採点した結果が並びます。さらに `YOUR FEEDBACK` 欄から人間のコメントを足し、両方を SKILL.md 改善のインプットにします。

![eval-viewer アサーション結果: 必須セクションの存在チェック / 日付一致チェックなどが ✓ で表示され、下部に人間のフィードバック入力欄がある](./images/eval-viewer-assertions.png)

eval-viewer には **3 prompts × 2 modes = 6 件** が並びます。WITHOUT SKILL は盲検 A/B 比較の片割れとして置かれており（`agents/comparator.md` の Blind Comparator がどちらがスキル付きか伏せて勝者を判定します）、フィードバックは原則 **WITH SKILL のみ** に書きます。WITHOUT を見て「想定以上に良い / 悪い」「Comparator の判定と感覚がズレる」と感じた時だけ、その違和感を書き残してください ── アサーション設計やスキル要否を見直すシグナルになります。

各ケースを Next で送って全件レビューしたら **Submit All Reviews** で確定し、出力されたフィードバックを Claude Code に貼り戻して SKILL.md 改稿に進みます。

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
