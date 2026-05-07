# claude-code/ ドキュメント執筆ガイド

`claude-code/` 配下の Markdown を編集したら、必ずリポジトリルートで `pnpm run lint`（cspell / textlint / prettier --check）を実行し、エラーが出たら修正してから完了とする。Prettier の整形と textlint の自動修正は `pnpm run fix` で当てられる。
