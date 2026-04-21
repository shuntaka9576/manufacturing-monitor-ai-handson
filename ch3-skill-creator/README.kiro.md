# ch3-skill-creator: Agent Skills - skill-creator によるスキル開発（Kiro IDE 版）

Claude Code で進めたい方は [README.claude.md](./README.claude.md) を参照してください。

## 概要

ch2 で構築した設備ダッシュボードをそのまま題材に、以下の2つを体験します。

### 1. セキュアなスキル導入フロー（pnpm + skills CLI）

外部スキルの導入は**サプライチェーン攻撃の入口**になりえます。本章では `vercel-labs/skills` の `skills` CLI を `pnpm` の devDependency として固定し、Anthropic 公式の `skill-creator` スキルを導入するまでの流れを体験します。

- **pnpm の `minimum-release-age`** — 公開から一定期間経過していないバージョンの取得をレジストリ側で拒否（今回は 21 日 = 30240 分）
- **`pnpm-lock.yaml` の `integrity`** — CLI の tarball ハッシュを固定
- **`skills-lock.json`** — 取得したスキルの source とファイル内容ハッシュ（SHA-256）を記録
- **`.kiro/skills/` を git 管理** — スキル本体の変更は PR で差分レビュー
- **`pnpm dlx` / `npx` を使わない** — レジストリに毎回問い合わせる運用を避け、`pnpm exec -- skills` でローカル固定版を起動

### 2. Agent Skills の作成・改善サイクル（skill-creator）

Agent Skills は、AI エージェントに新しい能力を追加するためのポータブルな命令パッケージです（[agentskills.io](https://agentskills.io) 標準）。Kiro では `.kiro/skills/<name>/SKILL.md` を配置するだけで、コンテキストに応じて自動的にスキルが活性化します。

1. **Discovery（発見）**: 起動時にスキル名と説明のみを読み込む（〜100 語/skill）
2. **Activation（活性化）**: リクエストがスキルの説明にマッチすると、本文全体を読み込む
3. **Execution（実行）**: `scripts/` や `references/` を必要に応じて読み込む

本章では `skill-creator` を使って **設備稼働日報を出力する自作スキル（daily-operations-report）** を作成し、Progressive Disclosure（Level 1/2/3）を意識したレビューサイクルでスキルを改善します。

### やること

- skills CLI のセキュアな導入（devDependency 固定・`minimum-release-age` ・lockfile 検査）
- `anthropics/skills` から `skill-creator` のインポート
- `skill-creator` で `daily-operations-report` スキルを対話的に作成
- 出力した日報の確認 → `skill-creator` でレビュー → Level 1/2/3 の改善を適用
- 改善後のスキルで再実行し、トリガー精度・出力品質の変化を観察

## 前提

- ch2 で作成した設備ダッシュボード（`app.py`, `pages/01_equipment_dashboard.py`）が存在する
- **Node.js 22 LTS 以上 / pnpm 10.16 以上**（`minimum-release-age` に対応した版が必要）
- Kiro IDE がインストール済み

`node -v` / `pnpm -v` で確認してください。pnpm の導入方法は [SETUP.kiro.md](../SETUP.kiro.md) を参照。

## 0. 環境セットアップ（約3分｜経過 約3分）

### 0.1. 章ディレクトリに移動

この章は専用の Node / Python 設定を持ちます。**必ず章ディレクトリを Kiro のワークスペースとして開いて**作業してください。

```bash
cd ch3-skill-creator
```

### 0.2. Streamlit アプリケーションの起動（ch2 完成状態の確認）

```bash
uv sync
uv run python db/seed.py
uv run streamlit run app.py
```

`http://localhost:8501` でダッシュボードが表示されることを確認してください（ch2 と同じ内容）。

### 0.3. モード選択

- Vibe モードを選択
- モデルが Opus 4.6 になっていることを確認

## 1. skills CLI をセキュアに導入する（約8分｜経過 約11分）

### 1.1. `package.json` と `.npmrc` を確認

章ディレクトリには以下の 2 ファイルが配置済みです。

`package.json`:

```json
{
  "name": "ch3-skill-creator",
  "private": true,
  "packageManager": "pnpm@10.33.0",
  "devDependencies": {
    "skills": "1.4.6"
  }
}
```

- `skills` は `vercel-labs/skills` の npm パッケージ（Agent Skills の導入・管理 CLI）
- バージョンは **exact pin**（プレフィックスなし）

`.npmrc`:

```
minimum-release-age=30240
```

- pnpm 10.16+ で追加された機能。単位は**分**（30240 分 = 21 日）。**指定期間未満のバージョンは `pnpm install` がレジストリ側で拒否**される
- サプライチェーン攻撃は「公開直後の悪意あるバージョンを自動取得させる」手口が多く、クールダウン期間を強制することで検知・削除の時間を稼ぐ

### 1.2. `minimum-release-age` が効くことを確認（学習目的の検証）

`package.json` を一時的に最新版に書き換えて挙動を確かめます。

```bash
pnpm pkg set "devDependencies.skills=^1.5.1"
pnpm install
```

次のようなエラーで拒否されます。

```
ERR_PNPM_NO_MATURE_MATCHING_VERSION  Version 1.5.1 (released N days ago) of skills does not meet the minimumReleaseAge constraint
```

pnpm は「何日前リリースか」を明示してくれます。確認できたら元に戻します。

```bash
pnpm pkg set "devDependencies.skills=1.4.6"
```

#### チェック項目

- [ ] `^1.5.1` で `ERR_PNPM_NO_MATURE_MATCHING_VERSION` エラーが出ること
- [ ] `1.4.6` に戻せていること

### 1.3. `pnpm install` で CLI を取得

```bash
pnpm install
```

`pnpm-lock.yaml` に `skills` の `resolution.integrity: sha512-...` が記録されます。

```bash
cat pnpm-lock.yaml
```

#### チェック項目

- [ ] `node_modules/skills/` が作成されていること
- [ ] `pnpm-lock.yaml` に `skills@1.4.6` と `integrity` フィールドが存在すること
- [ ] CLI が起動できること: `pnpm exec -- skills --version`（`1.4.6` と表示される）

### 1.4. `skill-creator` を `anthropics/skills` から導入

`pnpm exec` で `node_modules/.bin/skills` を起動します。`pnpm exec` は対象コマンドがローカルに無ければ registry にフェッチせずエラー終了する **fail-closed** 挙動です。Kiro 向けには `-a kiro-cli` を指定します。

```bash
pnpm exec -- skills add anthropics/skills --skill skill-creator -a kiro-cli -y
```

> [!WARNING]
> 以下は **registry fallback により `minimum-release-age` を迂回する** ため、このハンズオンでは使わないでください。
>
> - `pnpm dlx skills ...` — 設計上 registry から取得
> - `npx skills ...` — 非対話モードでは **無警告で最新版を取得**（検証済み：PATH/globals に CLI が無い状態で `1.5.1` が silently 取得された）。対話モードでも "Ok to proceed?" が出るだけなので、**絶対に `y` を押さない**

- `-a kiro-cli` — Kiro の `.kiro/skills/` に展開
- `-y` — プロンプトをスキップ（CI/CD 向け）
- インストール中に **Security Risk Assessment**（Gen / Socket / Snyk）が表示されるので確認

完了すると、次の 2 つが生成されます。

- `.kiro/skills/skill-creator/` — スキル本体
- `skills-lock.json` — 取得元とハッシュの記録

#### チェック項目

- [ ] `.kiro/skills/skill-creator/SKILL.md` が存在すること
- [ ] `skills-lock.json` に以下が記録されていること

```json
{
  "version": 1,
  "skills": {
    "skill-creator": {
      "source": "anthropics/skills",
      "sourceType": "github",
      "computedHash": "<SHA-256>"
    }
  }
}
```

> [!IMPORTANT]
> `skills-lock.json` の `computedHash` は**記録用**であり、後続の `skills add` や `skills experimental_install` では検証に使われません（不一致でもサイレントに上書きされます）。改ざん検知は **`.kiro/skills/` と `skills-lock.json` を git 管理し、PR で差分をレビュー** することで担保してください。

### 1.5. Kiro でスキルが認識されることを確認

Kiro を再起動し、「Agent Steering & Skills」パネルに `skill-creator` が表示されていること、およびチャットで `/` を入力したときに補完候補に出てくることを確認します。

#### チェック項目

- [ ] 「Agent Steering & Skills」パネルに `skill-creator` が並んでいること
- [ ] `/` 補完に `skill-creator` が表示されること

## 2. 「稼働日報生成スキル」の初版を作成する（約8分｜経過 約19分）

ch2 の SQLite DB（`data/factory.db`）を題材に、**指定日 24 時間分の設備稼働レポート**を Markdown で出力するスキルを作ります。

> [!NOTE]
> seed データ（`sample_data.xlsx`）は **2026-03-01 〜 2026-03-08** の固定期間なので、本章では対象日を **2026-03-07** に固定します。実運用スキルでは「昨日」を既定にしつつ、任意の対象日を引数で受けられるよう設計するのが良いでしょう（Phase 6 の発展課題参照）。

### 2.1. skill-creator に依頼

Kiro のチャットで以下を入力します。

```text
/skill-creator を使って、以下の要件のスキルを作成してください。

- スキル名: daily-operations-report
- 目的: data/factory.db から指定日 24 時間分の設備稼働データを集計し、日報を Markdown で出力する（既定の対象日は 2026-03-07、任意日を引数で受け取れる設計）
- 集計内容:
  - 設備別の稼働時間 / 停止時間 / 異常停止件数
  - 期間中の総生産数
  - 主要センサー値（temperature, vibration など）の平均/最大
- 出力: `reports/YYYY-MM-DD-operations.md` に保存
- 実装先: .kiro/skills/daily-operations-report/ 配下
```

skill-creator が対話でヒアリングしてきたら、**あえて最小限の情報だけ答えて**先に進めます（わざと粗い初版を作るため）。

### 2.2. 生成されたスキルを確認

```bash
ls .kiro/skills/daily-operations-report/
cat .kiro/skills/daily-operations-report/SKILL.md
```

#### チェック項目

- [ ] `.kiro/skills/daily-operations-report/SKILL.md` が存在すること
- [ ] description が曖昧、SQL/Python が SKILL.md 本文に直書き、scripts 未分離 ── といった「太った初版」になっていること（後でレビューで改善します）

## 3. 初版で日報を出力する（約3分｜経過 約22分）

Kiro のチャットで以下を入力します。

```text
2026-03-07 の稼働日報を出力してください
```

`daily-operations-report` スキルが自動でトリガーされ、`reports/2026-03-07-operations.md` が生成されます。

### チェック項目

- [ ] 指定ディレクトリに日報 `.md` が生成されていること
- [ ] 設備別の稼働率・停止件数・生産数が含まれていること

## 4. skill-creator でレビュー & 改善（約8分｜経過 約30分）

Agent Skills は 3 つの Level で遅延ロードされる設計です（Progressive Disclosure）。

- **Level 1 / Metadata**（name + description）— 起動時に**全スキル分**が system prompt に常駐。〜100 語/skill に抑える
- **Level 2 / SKILL.md 本文** — trigger 時のみ全文ロード。**500 行未満**が推奨
- **Level 3 / Bundled Resources**（`scripts/`, `references/`, `assets/`） — 本文から参照された時だけ読込。**scripts は実行のみで context を食わない**

重い情報を Level 3 に退避するのが鉄則です。skill-creator にレビューを依頼します。

> [!NOTE]
> **なぜ skill-creator は初版で綺麗に作ってくれないのか（マッチポンプ疑惑）**
>
> 「新規生成の時点で Progressive Disclosure を満たしてくれればレビュー不要では？」は正当な疑問です。しかし、この 2 パス構造は skill-creator の限界ではなく、**情報が生成行為によってしか現れない問題に対する合理的設計**と見るのが正確です。
>
> 1. **初版作成時には配置判断の根拠が存在しない** — 「何が重くて何を分離すべきか」を決めたくても、SQL の具体形も SKILL.md 本文の量もまだ存在しない。分離点を決める材料がない。
> 2. **生成した成果物そのものが、次パスの入力コンテキストになる** — 一度作って実体（Level 2 の膨らみ方、scripts に出せる純粋コード、references に出せる仕様情報）を手に入れて、はじめて最適配置を判断できる。
> 3. **ソフトウェア設計で見慣れたパターン** — Spike → Refactor / 下書き → 推敲 / Actor-Critic / Reflection loops。いずれも「作ってみないと構造が決まらない問題」を 2 パスで解く手法。
> 4. **教育的デザインとしても意図的** — Phase 2 で「わざと粗い初版を作る」と明示しており、**差分**（初版 → 改善版）を体験させることが狙い。
>
> 実運用でも「生成 → 実測 → 構造化」のサイクルは有効です。AI が作るスキルも、生成したものを実測して構造を整える工程があってはじめて筋の通った資産になる、という学びを持ち帰ってください。

### 4.1. レビュー依頼

> [!IMPORTANT]
> Kiro では **Spec モード**（あるいは変更前に必ず確認するモード）でレビューを依頼してください。skill-creator が提案した内容を吟味してから適用するのがこのフェーズの学びです。即時適用モードで実行すると、何を改善したかの観察機会が失われます。

```text
/skill-creator で .kiro/skills/daily-operations-report/ をレビューして、気になった点を改善してください。
```

観点を人間側から指示する必要はありません。Progressive Disclosure の評価は skill-creator 自身が持つべき知識です。skill-creator が差分を提案してきたら、**どのレベルの問題をどう指摘してきたか**に注目しつつ適用してください。

### 4.2. 改善後の構造を確認

期待される構成例:

```
.kiro/skills/daily-operations-report/
├── SKILL.md                      # Level 2: 高レベルガイド (短く保つ)
├── references/
│   └── schema.md                 # Level 3: DB スキーマ・SQL サンプル
├── scripts/
│   └── aggregate.py              # Level 3: 集計ロジック本体
└── assets/
    └── report-template.md        # Level 3: 出力テンプレート
```

### チェック項目

- [ ] description が「日報を出力したいときに使う」と明確に伝わる記述になっていること
- [ ] SKILL.md 本文が大幅に短くなっていること
- [ ] `scripts/aggregate.py` が分離されていること
- [ ] `references/` または `assets/` に詳細が退避されていること

### 4.3. 改善版で再実行

```text
2026-03-07 の稼働日報を出力してください
```

同じプロンプトで再生成し、トリガー精度・出力品質の変化を観察します。

## 5. 検証（約3分）

#### チェック項目

- [ ] `package.json` の `devDependencies.skills` が exact pin されていること
- [ ] `.npmrc` に `minimum-release-age=30240` が記載されていること
- [ ] `pnpm-lock.yaml` と `skills-lock.json` が生成・コミット可能な状態であること
- [ ] `.kiro/skills/skill-creator/` と `.kiro/skills/daily-operations-report/` が存在すること
- [ ] 改善後の `daily-operations-report` が Progressive Disclosure の 3 レベルを活用した構造になっていること

## 6. 時間が余ったら

### 6.1. `skills check` でリモート更新を検出する

```bash
pnpm exec -- skills check
```

`skills check` は**リモート側の新バージョン有無**を検出するコマンドです（ローカル改ざん検知ではない）。upstream の `anthropics/skills` に更新がある場合、ここで通知されます。必要なら `skills update` で最新化します。

### 6.2. 自作スキルを社内配布する想定で再設計する

`daily-operations-report` を社内チームに配布する前提で、skill-creator に以下の追加機能を相談してみてください。

- 引数で対象日・対象設備を受け取れるようにする
- 出力形式を MD/CSV/HTML に切り替え可能にする
- `allowed-tools` を絞り、DB 読み取り専用の実行権限にする
