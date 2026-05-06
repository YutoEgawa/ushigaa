# ウシガー デプロイ手順

## 1. 利用サービス

- Database: Supabase
- Backend API: FastAPI を実行できるホスティングサービス
  - 例: Render, Fly.io, Railway など
- Frontend: 静的サイトホスティング
  - 例: Vercel, Netlify, Cloudflare Pages など
- Mail: SendGrid
- Domain/DNS: 独自ドメインを使う場合はドメイン管理サービス

## 2. Supabase

1. 本番で使う Supabase Project を決める。
2. `active_legislators`, `parties`, `districts` など、API が参照するテーブル/ビューが本番データになっていることを確認する。
3. API 用に `SUPABASE_URL` と `SUPABASE_ANON_KEY` を控える。
4. Supabase 側で anon key に不要な更新権限がないことを確認する。

## 3. Backend API

Render service name: `Ushigaa`

FastAPI の起動コマンド:

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

本番環境変数:

```bash
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
ALLOWED_ORIGINS=https://ushigaa.com,https://www.ushigaa.com
CONTACT_RECIPIENT_EMAIL=y.egawa.ahstu0415@gmail.com
SENDGRID_API_KEY=...
SENDGRID_FROM_EMAIL=...
SENDGRID_FROM_NAME=ウシガー
```

デプロイ後の確認:

```bash
curl https://<api-domain>/v1/health
curl https://<api-domain>/v1/legislators?limit=1
```

## 4. Frontend

Cloudflare Pages project name: `ushigaa`

フロントエンドは静的SPAなので、`frontend/` を公開ディレクトリとしてホスティングする。

本番公開時は `frontend/config.js` の API URL を本番APIへ差し替える。

```js
window.USHIGA_API_BASE = "https://api.ushigaa.com/v1";
```

公開後の確認:

- トップページが表示される
- 議員検索が本番APIのデータを返す
- 議員詳細ページに遷移できる
- 問い合わせフォーム送信後に完了文言が表示される

## 5. SendGrid

1. SendGrid で送信元メールアドレスまたはドメインを認証する。
2. API Key を発行する。
3. Backend の環境変数 `SENDGRID_API_KEY` と `SENDGRID_FROM_EMAIL` に設定する。
4. 問い合わせフォームからテスト送信し、`CONTACT_RECIPIENT_EMAIL` に届くことを確認する。

## 6. 独自ドメイン

1. フロントエンド用ドメインを設定する。
2. API 用のサブドメインを設定する。
   - `api.ushigaa.com`
3. HTTPS が有効になっていることを確認する。
4. フロントエンドの `config.js` が HTTPS の API URL を参照していることを確認する。

## 7. 公開前チェック

- `python -m pytest`
- `node --check frontend/src/app.js`
- API `/v1/health` が成功する
- API `/v1/legislators?limit=1` が成功する
- トップページ、検索結果、議員詳細、About、問い合わせ、利用規約、プライバシーポリシーを確認する
- 問い合わせフォームの送信テストを行う
- スマホ幅で表示崩れがないか確認する
- 未取得データが「衆議院や参議院、政党HPに記載なし」等の方針に沿って表示されることを確認する
