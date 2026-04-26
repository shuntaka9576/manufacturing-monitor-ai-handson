---
paths:
  - "ch3-skill-creator/**/*"
---

# ch3-skill-creator: Agent Skills - skill-creator によるスキル開発 - 実装仕様

## 章の構成

**前半（Phase 0〜5）**: Claude Code 公式マーケットプレイスから skill-creator を導入 → 設備稼働日報スキルを構築 → Progressive Disclosure でレビュー改善 → AskUserQuestion を組み込み

**後半（Phase 6〜7）**: サードパーティ製スキル管理ツール（`gh skill`）を紹介

## 追加ファイル（章ディレクトリ）

```
ch3-skill-creator/
├── .claude/skills/                # Claude Code 版
│   ├── skill-creator/             # 公式マケプレから /plugin install で導入
│   └── daily-operations-report/   # skill-creator で自作
├── .kiro/skills/                  # Kiro 版（Kiro を使う場合）
│   ├── skill-creator/
│   └── daily-operations-report/
└── (ch2 の全ファイル)
```

**本章で新たに生成するのは `.claude/skills/` と `reports/` のみ**。pnpm / npm 関連ファイル（package.json, .npmrc, pnpm-lock.yaml, node_modules, skills-lock.json）は一切扱わない。

## スキルセットアップ手順

### Claude Code 版（公式マケプレ経由）

```text
/plugin marketplace add anthropics/skills
/plugin install skill-creator@anthropic-agent-skills
```

- `anthropics/skills` の `.claude-plugin/marketplace.json` で marketplace 名は `anthropic-agent-skills`
- バージョン固定したい場合は `anthropics/skills#v1.0.0` のようにタグを指定して marketplace を追加

### Kiro 版

Kiro の plugin/marketplace 対応状況は別途確認。未対応なら後半の `gh skill` を主導線にする選択肢も検討。

## ハンズオンフェーズ

### Phase 0: 環境確認

- `uv sync && uv run python db/seed.py && uv run streamlit run app.py` でダッシュボードが動く

### Phase 1: skill-creator を公式マケプレから導入

| 確認項目                   | 使用コマンド                                                      |
| -------------------------- | ----------------------------------------------------------------- |
| マーケットプレイス追加     | `/plugin marketplace add anthropics/skills`                       |
| マーケットプレイス登録確認 | `/plugin marketplace list`（`anthropic-agent-skills` が出ること） |
| skill-creator インストール | `/plugin install skill-creator@anthropic-agent-skills`            |
| インストール結果確認       | `/plugin list`（enabled 表示）／`/` 補完で `skill-creator` 表示   |

**ねらい**: 追加ツール不要で Anthropic 公式スキルを入れる公式導線を体験する。

### Phase 1.6: 組み込みサブエージェントで仕様調査

| 確認項目                                     | 使用コマンド                                                                                       |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| claude-code-guide 呼び出し（Claude Code 版） | チャットに「claude-code-guide を使って、SKILL.md frontmatter と AskUserQuestion の使い方を教えて」 |
| 別タスク表示（Claude Code 版）               | UI に `Task(claude-code-guide)` ブロックが折り畳み表示される                                       |
| Vibe モードでの同等調査（Kiro 版）           | チャットに同等プロンプトを投げて、frontmatter と askQuestions 相当の情報を取得                     |

**ねらい**: built-in subagent（Claude Code）でメインセッションのコンテキストを汚さず仕様調査する体験。

### Phase 1.7: 対話確認ツールを直接体験

| 確認項目                                         | 期待結果                                                           |
| ------------------------------------------------ | ------------------------------------------------------------------ |
| Claude Code 版: `AskUserQuestion` を直接呼ばせる | 出力先・フォーマット・閾値など 3 問を選択肢 UI で聞かれる          |
| Kiro 版: `askQuestions` 相当を呼ばせる           | 同等の 3 問を UI で聞かれる                                        |
| 余計な実装に進まないこと                         | 回答後、「了解しました」程度の返答で止まり、スキル作成は後段で実施 |

**ねらい**: スキルに組み込ませる前に、ツール本体の挙動を手で触る。

### Phase 2: 「稼働日報生成スキル」初版作成

| 確認項目                 | 使用コマンド                                                                                         |
| ------------------------ | ---------------------------------------------------------------------------------------------------- |
| skill-creator の呼び出し | Claude Code / Kiro のチャットから `/skill-creator`                                                   |
| スキル生成               | `.claude/skills/daily-operations-report/SKILL.md` or `.kiro/skills/daily-operations-report/SKILL.md` |
| 「太った初版」の確認     | description が曖昧・SQL 直書き・scripts 未分離                                                       |

### Phase 3: 日報出力

| 確認項目     | 使用コマンド                                                                                          |
| ------------ | ----------------------------------------------------------------------------------------------------- |
| 自動トリガー | チャットに「2026-03-07 の稼働日報を出力してください」（seed データが 2026-03 固定のため対象日を固定） |
| 出力ファイル | `reports/2026-03-07-operations.md`                                                                    |

### Phase 4: Progressive Disclosure レビュー

| 改善レベル | 対象                               | 期待結果                               |
| ---------- | ---------------------------------- | -------------------------------------- |
| Level 1    | description                        | 「いつ使うか」が明確                   |
| Level 2    | SKILL.md 本文                      | 500 行未満、high-level guide 化        |
| Level 3    | `scripts/` `references/` `assets/` | 集計ロジック・テンプレ・スキーマを分離 |

### Phase 4.4: 対話確認の追加

| シナリオ               | 期待結果                                                        |
| ---------------------- | --------------------------------------------------------------- |
| 対象日未指定           | seed データ期間（2026-03-01〜2026-03-08）から選択肢 UI を提示   |
| 既存レポートと同じ日付 | 「上書き / 別名で保存 / 中断」の 3 択 UI を提示                 |
| スキル本体への組み込み | `SKILL.md` もしくは `scripts/` に対話ツール呼び出しが記述される |

### Phase 5: 前半の検証

- `/plugin marketplace list` に `anthropic-agent-skills` がある
- `/plugin list` に `skill-creator@anthropic-agent-skills` が enabled で表示
- `.claude/skills/daily-operations-report/` が Progressive Disclosure 構造で保存されている
- `AskUserQuestion` による対話確認が組み込まれている
- `claude-code-guide` を 1 回以上呼び出して仕様調査している
- Phase 1.7 で対話確認ツールを直接呼び UI を目視確認している

### Phase 6: gh skill で外部スキル管理

| 確認項目                        | 使用コマンド                                                                      |
| ------------------------------- | --------------------------------------------------------------------------------- |
| 他スキルを pin 付きインストール | `gh skill install anthropics/skills mcp-builder --agent claude-code --pin <タグ>` |
| インストール済み一覧            | `gh skill list`                                                                   |
| 更新                            | `gh skill update --all`                                                           |
| 削除                            | `gh skill uninstall <owner>/<repo> <skill>`                                       |

**ねらい**: 非公式 GitHub リポジトリや、公式マケプレに無いスキルを pin 固定で導入する手順を体験。

### Phase 7: まとめ

- **第一選択は Claude Code 公式マケプレ**
- サードパーティ GitHub スキルは `gh skill` で pin 導入

## 検証項目（章全体）

- `.claude/skills/skill-creator/SKILL.md` が公式マケプレ経由で配置されている
- 自作 `daily-operations-report` が Progressive Disclosure を活用した構造で保存されている
- `daily-operations-report` に対話確認（AskUserQuestion / askQuestions 相当）が組み込まれている
- Claude Code 版では `claude-code-guide` を 1 回以上呼び出して仕様調査している
- Phase 1.7 で対話確認ツールを直接呼び、選択肢 UI を目視で確認している
- （後半）`gh skill` で外部スキルの導入手順を実行している
