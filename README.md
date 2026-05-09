# ウシガー

国会議員データベースの開発用リポジトリです。

## Current Status

- Supabase `kokkai-giin-db` に両院データ投入済み
- `legislators`: 712件
- `legislator_terms`: 712件
- `parties`: 15件
- `districts`: 346件

## Backend

```bash
cp .env.example .env
# .env の SUPABASE_ANON_KEY を設定
uvicorn app.main:app --app-dir backend --reload
```

API docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Contract: `docs/api.md`

## Frontend

Figma案をベースにした静的SPAです。依存パッケージなしで動きます。

```bash
/Users/y.egawa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m http.server 5173 --directory frontend
```

- App: `http://127.0.0.1:5173/`
- API: `http://127.0.0.1:8000/v1`

バックエンド未起動時は、画面確認用のフォールバックデータを表示します。

本番公開時は `frontend/config.js` の `window.USHIGA_API_BASE` が `https://api.ushigaa.com/v1` を向くようにします。
ローカル開発時は `frontend/config.local.example.js` の値を参考に `frontend/config.js` を一時的に戻します。

## Deployment

公開準備の手順は `docs/deployment.md` を参照してください。

## Data Import Helpers

```bash
/Users/y.egawa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_sangiin_import_sql.py
/Users/y.egawa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_shugiin_import_sql.py
```

国会APIの質疑データ用:

```bash
# 氏名照合の保存なし検証
/Users/y.egawa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/verify_kokkai_speeches.py --limit 5

# Supabase投入用SQLを生成（DBへ直接書き込まない）
/Users/y.egawa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_kokkai_speech_import_sql.py --limit 5
```
