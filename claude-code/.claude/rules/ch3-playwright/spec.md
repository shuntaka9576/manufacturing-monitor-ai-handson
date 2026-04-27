---
paths:
  - "ch3-playwright/**/*"
---

# ch3-playwright: Agent Skills - playwright-cliによるUI動作確認 - 実装仕様

## 追加ファイル

```
ch3-playwright/
├── .kiro/skills/              # Kiro版
│   └── playwright-cli/
│       └── SKILL.md
├── .claude/skills/            # Claude Code版
│   └── playwright-cli/
│       └── SKILL.md          # Microsoft公式 playwright-cli スキル
└── (ch2の全ファイル)
```

## スキルセットアップ

Kiro IDEの「Agent Steering & Skills」パネルからインポート。

- URL: `https://github.com/microsoft/playwright-cli/tree/main/skills/playwright-cli`
- 配置先: `.kiro/skills/playwright-cli/SKILL.md`

## UI動作確認フェーズ

### Phase 1: 画面表示の確認

| 確認項目               | 使用コマンド             |
| ---------------------- | ------------------------ |
| ダッシュボード初期表示 | `snapshot`, `screenshot` |
| 主要UI要素の存在確認   | `snapshot`               |
| JSエラーなし           | `console`                |

### Phase 2: 設備切り替えの確認

| 確認項目                   | 使用コマンド         |
| -------------------------- | -------------------- |
| 設備選択ドロップダウン操作 | `snapshot`, `select` |
| 切り替え前後のUI変化       | `screenshot`         |
| パラメータの動的変化       | `snapshot`           |

### Phase 3: 動画録画の確認

| 確認項目                   | 使用コマンド |
| -------------------------- | ------------ |
| 設備切り替え操作の動画録画 | `run-code`   |
| 録画ファイルの保存確認     | ファイル確認 |

## 検証

- playwright-cliスキルがKiroで認識されること
- 各フェーズでscreenshot/snapshotが取得できること
- consoleにJSエラーがないこと
