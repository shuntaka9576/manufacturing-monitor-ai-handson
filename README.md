# 製造設備モニタリングダッシュボード - AI駆動開発ハンズオン

製造業向け設備稼働状況可視化アプリを、AI駆動開発の手法で段階的に構築するハンズオン教材です。

本リポジトリは Kiro IDE 版と Claude Code（CLI）版を **完全に別ディレクトリ** で提供します。両者は別物として運用しており、章構成・セットアップ手順・ツール固有の操作はそれぞれ独立に管理しています。最初にどちらのツールで進めるかを選び、以降は対応するディレクトリだけを参照してください。

## ツールを選ぶ

- Kiro IDE で進めたい人 → [`kiro/`](./kiro/README.md)
- Claude Code（CLI）で進めたい人 → [`claude-code/`](./claude-code/README.md)

それぞれのディレクトリ直下に `SETUP.md`（セットアップガイド）と各章（`ch1/`, `ch2/`, ...）が揃っています。

![全体像](assets/root/all.png)

## ディレクトリ構成

```
manufacturing-monitor-ai-handson/
├── README.md         # このファイル（入口・ツール選択ガイド）
├── assets/           # 共有画像（両ディレクトリから ../assets/ で参照）
├── tools/            # サンプル Excel 生成ツールなどの共有ユーティリティ
├── kiro/             # Kiro IDE 版のセットアップ + 各章
│   ├── README.md
│   ├── SETUP.md
│   ├── ch1/ … ch5_fin/
│   └── works/
└── claude-code/      # Claude Code 版のセットアップ + 各章
    ├── README.md
    ├── SETUP.md
    ├── .claude/      # rules / skills（sync-chapters など）
    └── ch1/ … ch5_fin/（および ch3-playwright / ch3-skill-creator）
```

> [!NOTE]
> リポジトリ全体の lint / format（cspell・textlint・prettier）と Git フック（lefthook）はリポジトリ直下で一元管理しています。設定ファイルは `package.json` / `turbo.json` / `lefthook.yml` / `.cspell.json` / `.textlintrc.json` です。

> [!NOTE]
> 本ハンズオン全体で約100クレジットを使用します。

> [!WARNING]
> 各チャプターは続きから行うことを推奨します。これは LLM が非決定的な出力をした結果として進行が詰まる可能性があるためです。
