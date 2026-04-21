---
paths:
  - "ch3-skill-creator/**/*"
---

# ch3-skill-creator: Agent Skills - skill-creator によるスキル開発 - 実装仕様

## 追加ファイル

```
ch3-skill-creator/
├── package.json                   # skills CLI を devDependency で exact pin、packageManager: pnpm@x.y.z
├── pnpm-lock.yaml                 # integrity ハッシュつき（コミット対象）
├── .npmrc                         # minimum-release-age=30240（21日を分換算）
├── .gitignore                     # node_modules/
├── skills-lock.json               # ハンズオン中に生成（コミット対象）
├── .claude/skills/                # Claude Code 版
│   ├── skill-creator/             # skills CLI で導入
│   └── daily-operations-report/   # skill-creator で自作
├── .kiro/skills/                  # Kiro 版（Kiro を使う場合）
│   ├── skill-creator/
│   └── daily-operations-report/
└── (ch2 の全ファイル)
```

## 設定ファイルの仕様

### package.json

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

- `skills` は `vercel-labs/skills` の npm パッケージ（Agent Skills 導入・管理 CLI）
- **exact pin**（プレフィックス無し）または `^` で指定
- `scripts` は受講者が直接コマンドを打つ体験を重視し、事前定義しない

### .npmrc

```
minimum-release-age=30240
```

- pnpm 10.16+ の機能。単位は**分**（30240 分 = 21 日）。公開指定期間未満のバージョンを `pnpm install` がレジストリ側で拒否

## スキルセットアップ手順

### Claude Code 版

```bash
pnpm install                                                                 # CLI と依存を lockfile 通りに取得
pnpm exec -- skills add anthropics/skills --skill skill-creator -a claude-code -y
```

- 配置先: `.claude/skills/skill-creator/`
- `skills-lock.json` が自動生成される

### Kiro 版

```bash
pnpm install
pnpm exec -- skills add anthropics/skills --skill skill-creator -a kiro-cli -y
```

- 配置先: `.kiro/skills/skill-creator/`

## ハンズオンフェーズ

### Phase 0: 環境確認

- `node -v` が 22.x 以上、`pnpm -v` が 10.16 以上
- `uv sync && uv run python db/seed.py && uv run streamlit run app.py` でダッシュボードが動く

### Phase 1: skills CLI のセキュアな導入

| 確認項目 | 使用コマンド |
| --- | --- |
| `minimum-release-age` が効くこと | `pnpm pkg set "devDependencies.skills=^1.5.1" && pnpm install` で `ERR_PNPM_NO_MATURE_MATCHING_VERSION` |
| CLI のインストール | `pnpm install` |
| integrity ハッシュの固定 | `cat pnpm-lock.yaml` |
| skill-creator の導入 | `pnpm exec -- skills add anthropics/skills --skill skill-creator -a <agent> -y` |
| skills-lock.json 生成 | `cat skills-lock.json` |

### Phase 1.6: 組み込みサブエージェントで仕様調査

| 確認項目 | 使用コマンド |
| --- | --- |
| claude-code-guide 呼び出し（Claude Code 版） | チャットに「claude-code-guide を使って、SKILL.md frontmatter と AskUserQuestion の使い方を教えて」 |
| 別タスク表示（Claude Code 版） | UI に `Task(claude-code-guide)` ブロックが折り畳み表示される |
| Vibe モードでの同等調査（Kiro 版） | チャットに同等プロンプトを投げて、frontmatter と askQuestions 相当の情報を取得 |

**ねらい**: built-in subagent（Claude Code）でメインセッションのコンテキストを汚さず仕様調査する体験。Kiro には同等の built-in が無いため、チャットで直接聞く形となり、サブエージェント有無の差を体感できる。

### Phase 1.7: 対話確認ツールを直接体験

| 確認項目 | 期待結果 |
| --- | --- |
| Claude Code 版: `AskUserQuestion` を直接呼ばせる | 出力先・フォーマット・閾値など 3 問を選択肢 UI で聞かれる |
| Kiro 版: `askQuestions` 相当を呼ばせる | 同等の 3 問を UI で聞かれる（Experimental のため代替テキスト確認でも可） |
| 余計な実装に進まないこと | 回答後、「了解しました」程度の返答で止まり、スキル作成は後段で実施 |

**ねらい**: スキルに組み込ませる前に、ツール本体の挙動（選択肢 UI、3 問一括、"Other" 自由入力）を手で触る。Phase 2 の「最小情報で粗い初版」フローを汚さないよう、ここでの回答は後段に引き継がない。

### Phase 2: 「稼働日報生成スキル」初版作成

| 確認項目 | 使用コマンド |
| --- | --- |
| skill-creator の呼び出し | Claude Code / Kiro のチャットから `/skill-creator` |
| スキル生成 | `.claude/skills/daily-operations-report/SKILL.md` or `.kiro/skills/daily-operations-report/SKILL.md` |
| 「太った初版」の確認 | description が曖昧・SQL 直書き・scripts 未分離 |

### Phase 3: 日報出力

| 確認項目 | 使用コマンド |
| --- | --- |
| 自動トリガー | チャットに「2026-03-07 の稼働日報を出力してください」（seed データが 2026-03 固定のため対象日を固定） |
| 出力ファイル | `reports/2026-03-07-operations.md` |

### Phase 4: Progressive Disclosure レビュー

| 改善レベル | 対象 | 期待結果 |
| --- | --- | --- |
| Level 1 | description | 「いつ使うか」が明確 |
| Level 2 | SKILL.md 本文 | 500 行未満、high-level guide 化 |
| Level 3 | `scripts/` `references/` `assets/` | 集計ロジック・テンプレ・スキーマを分離 |

### Phase 4.4: 対話確認の追加（AskUserQuestion / askQuestions）

| シナリオ | 期待結果 |
| --- | --- |
| 対象日未指定 | seed データ期間（2026-03-01〜2026-03-08）から選択肢 UI を提示 |
| 既存レポートと同じ日付 | 「上書き / 別名で保存 / 中断」の 3 択 UI を提示 |
| スキル本体への組み込み | `SKILL.md` もしくは `scripts/` に対話ツール呼び出しが記述される |

**ねらい**: 「最小の指示で動くスキル」→「実運用で任せられる対話型スキル」への進化を体感。Claude Code では `AskUserQuestion`、Kiro では `askQuestions`（Experimental）を想定。Kiro で UI が出ない場合は簡易実装で代替可とする。

### Phase 5: 改善版で再実行

- 同じプロンプトで再生成し、出力品質の向上を確認
- 対象日を省略したプロンプト、既存日付のプロンプトで対話確認 UI が出ることを確認

## skills-lock.json の扱い

- `source`, `sourceType`, `computedHash` を記録
- **改ざん検知には使えない**（`skills add` / `experimental_install` は既存ハッシュを検証せずサイレント上書きする）
- コミット対象とし、改ざん検知は git diff による PR レビューで担保

## 検証

- `package.json` の `skills` が exact / `^` でピン留めされていること
- `.npmrc` に `minimum-release-age=30240` が記載
- `pnpm-lock.yaml` に `skills` の `resolution.integrity: sha512-...` がある
- `skills-lock.json` に `source: "anthropics/skills"` と `computedHash` が記録されている
- `.claude/skills/skill-creator/SKILL.md` または `.kiro/skills/skill-creator/SKILL.md` が配置されている
- 自作 `daily-operations-report` が Progressive Disclosure を活用した構造で保存されている
- `daily-operations-report` に対話確認（AskUserQuestion / askQuestions 相当）が組み込まれている
- Claude Code 版では `claude-code-guide` を 1 回以上呼び出して仕様調査している
- Phase 1.7 で対話確認ツールを直接呼び、選択肢 UI を目視で確認している
