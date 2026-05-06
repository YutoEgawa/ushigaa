# Web Wireframes v2

> **このファイルについて**: `docs/wireframes.md` を改良したバージョン。
> 元のwireframes.mdは変更せず、本ファイルを新規作成。
> 主な追加・改善点:
> - ゲージ・カード・詳細ページの具体的なレイアウト仕様を追加
> - 空状態・ローディング状態のビジュアル仕様を追加
> - Figmaコンポーネントへの対応付けを強化
> - スペーシング・タイポグラフィトークンを追加

---

## Design Direction（変更なし）

Working concept: **Civic Strategy HUD**

The site should feel like a strategy game's command interface while remaining a neutral public-information tool. Use game-like panels, gauges, tabs, filters, and dense roster layouts. Do not use rankings, power scores, attack/defense language, or visual treatment that implies one party or legislator is better than another.

Core pages:

- `/` - 議員検索・一覧ページ
- `/search` - 検索結果ページ
- `/legislators/[id]` - `〇〇 衆議院議員` / `〇〇 参議院議員`

---

## Typography Tokens（新規追加）

| Token | Size | Weight | Line Height | Usage |
|---|---|---|---|---|
| `type-display` | 28px | 700 | 1.2 | ページ見出し |
| `type-title` | 20px | 600 | 1.3 | パネル見出し・議員氏名 |
| `type-subtitle` | 16px | 600 | 1.4 | カード見出し |
| `type-body` | 14px | 400 | 1.6 | 本文・説明 |
| `type-label` | 12px | 500 | 1.4 | ラベル・チップ |
| `type-mono` | 13px | 400 | 1.5 | 数値・ID・カウンター |
| `type-caption` | 11px | 400 | 1.4 | 補足・出典 |

フォント: `'Noto Sans JP', 'Inter', sans-serif`
数値専用: `'JetBrains Mono', 'Fira Code', monospace`

---

## Spacing Tokens（新規追加）

| Token | Value | Usage |
|---|---|---|
| `space-1` | 4px | インラインアイコンギャップ |
| `space-2` | 8px | チップ内パディング、コンパクト要素 |
| `space-3` | 12px | カード内パディング（タイト） |
| `space-4` | 16px | カード内パディング（標準） |
| `space-5` | 20px | セクション間の小さな余白 |
| `space-6` | 24px | パネル内パディング |
| `space-8` | 32px | セクション間余白 |
| `space-10` | 40px | ページレベルの大きな余白 |
| `space-12` | 48px | ページ上下のトップマージン |

Border radius: `2px`（HUDコンセプトに合わせシャープに統一）
Box shadow (glow): `0 0 0 1px var(--accent-cyan)` on focus/active

---

## Color Palette（変更なし・参照元）

元の`wireframes.md`の `## Color Palette` セクションを参照。
以下に使用ルールを補足する。

### 使用優先ルール

1. ページ背景は必ず `bg-canvas (#070A12)`
2. カード・パネルは `bg-surface (#101622)` または `bg-surface-raised (#172033)`
3. インタラクティブ要素のフォーカスリングは `accent-cyan (#38D5FF)` 1px glow
4. テキストは`text-primary` / `text-secondary` / `text-muted` の3段階を厳守
5. ゲージカラーは `gauge-1〜8` をシート数降順で割り当て（与野党問わず）

---

## Shared Layout

### Desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ SITE HUD BAR  (height: 56px, bg: bg-surface, border-bottom: line-subtle)    │
│ [ウシガー] (type-subtitle, text-primary, accent-cyan on hover)             │
│                                    [議員検索] [このサイトについて]            │
├──────────────────────────────────────────────────────────────────────────────┤
│ PAGE CONTENT  (max-width: 1200px, padding: 0 space-6)                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

Shared header behavior:
- Site name links to `/`
- Active nav item: bottom border 2px `accent-cyan`、text `text-primary`
- Inactive nav item: text `text-secondary`
- Avoid party-colored global navigation
- Keep labels utilitarian and neutral

### Mobile

```text
┌──────────────────────────────┐
│ [ウシガー]  (height: 52px)  │
│                         [☰]  │
├──────────────────────────────┤
│ PAGE CONTENT (padding: 0 16px)│
└──────────────────────────────┘
```

---

## `/` Top Page

Purpose: Let users immediately search the legislator database.

### Desktop Wireframe（詳細版）

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ ウシガー                                           議員検索  このサイト      │
├──────────────────────────────────────────────────────────────────────────────┤
│  padding-top: space-8                                                        │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ COMMAND SEARCH  (bg-command, border: line-subtle, padding: space-6)    │  │
│  │                                                                        │  │
│  │ > ┌──────────────────────────────────────────┐ ┌─────────────────┐    │  │
│  │   │ 氏名・よみ・政党・選挙区で検索           │ │    検索         │    │  │
│  │   │ (type-body, text-muted as placeholder)   │ │ (accent-cyan bg)│    │  │
│  │   └──────────────────────────────────────────┘ └─────────────────┘    │  │
│  │                                                                        │  │
│  │ [すべて]  [衆議院]  [参議院]   ← HouseSegmentedControl                │  │
│  │ (chip style, default/active state)                                     │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  margin-top: space-8                                                         │
│  POWER MAP STRIP  ─────────────────────────────────────────────────────────  │
│  ┌──────────────────────────────────────┐ ┌────────────────────────────────┐ │
│  │ 衆議院 勢力図                         │ │ 参議院 勢力図                   │ │
│  │ (HudPanel, padding: space-6)          │ │ (HudPanel, padding: space-6)   │ │
│  │                                      │ │                                │ │
│  │   ╭──────────────────────╮           │ │  ╭──────────────────────╮      │ │
│  │  ╱ [gauge-1][gauge-2]... ╲           │ │ ╱ [gauge-1][gauge-2]... ╲     │ │
│  │ ╱_________________________╲          │ │╱_________________________╲     │ │
│  │           │ ← 白い過半数マーカー      │ │          │ ← 白い過半数マーカー│ │
│  │                                      │ │                                │ │
│  │  与党: 261 / 465  過半数: 233         │ │ 与党: 143 / 248  過半数: 125    │ │
│  │  ● 過半数到達: はい                   │ │ ● 過半数到達: はい               │ │
│  │  [凡例: ■自民 ■立憲 ■維新 ...]        │ │ [凡例: ■自民 ■立憲 ■公明 ...]   │ │
│  └──────────────────────────────────────┘ └────────────────────────────────┘ │
│                                                                              │
│  margin-top: space-6                                                         │
│  STATS COUNTER GRID  ──────────────────────────────────────────────────────  │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ │
│  │ 衆議院          │ │ 参議院          │ │ 合計            │ │ 政党・会派      │ │
│  │ 465             │ │ 247             │ │ 712             │ │ 15              │ │
│  │ (type-mono, 32px│ │ (same)          │ │ (same)          │ │ (same)          │ │
│  └────────────────┘ └────────────────┘ └────────────────┘ └────────────────┘ │
│                                                                              │
│  margin-top: space-6                                                         │
│  ┌──────────────────────────────┐ ┌───────────────────────────────────────┐  │
│  │ QUICK FILTERS (HudPanel)      │ │ ROSTER PREVIEW (HudPanel)             │  │
│  │                               │ │                                       │  │
│  │ 院           [すべて][衆][参]  │ │ 氏名          院  政党      選挙区     │  │
│  │ 政党・会派   [select ▼]        │ │ ─────────────────────────────────── │  │
│  │ 選挙区       [select ▼]        │ │ 逢沢 一郎     衆  自民      岡山1区   │  │
│  │ 区分         [すべて][小][比]  │ │ 青木 愛       参  立憲      比例      │  │
│  │                               │ │ 青木 一彦     参  自民      鳥取・島根 │  │
│  │ [条件をクリア]                 │ │ ...                                   │  │
│  │                               │ │                                       │  │
│  │                               │ │          [全議員を検索 →]             │  │
│  └──────────────────────────────┘ └───────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Wireframe（詳細版）

```text
┌──────────────────────────────┐
│ ウシガー              [☰]  │
├──────────────────────────────┤
│ padding: space-4             │
│                              │
│ COMMAND SEARCH               │
│ ┌──────────────────────────┐ │
│ │ 氏名・よみ・政党・選挙区 │ │
│ └──────────────────────────┘ │
│ [すべて] [衆] [参]           │
│ [検索 ─────────────────────] │
│                              │
│ margin-top: space-6          │
│ 衆議院 勢力図                 │
│ ┌──────────────────────────┐ │
│ │  ╭──────────────────╮    │ │
│ │ ╱  [arcs...]         ╲   │ │
│ │╱______________________|   │ │
│ │  与党: 261  過半数: 233  │ │
│ │  ● 過半数到達: はい      │ │
│ │  [凡例 (2col grid)]     │ │
│ └──────────────────────────┘ │
│                              │
│ 参議院 勢力図                 │
│ ┌──────────────────────────┐ │
│ │  (同上構成)              │ │
│ └──────────────────────────┘ │
│                              │
│ STATS (2x2 grid)             │
│ ┌──────────┐ ┌──────────┐   │
│ │ 衆院 465  │ │ 参院 247  │   │
│ └──────────┘ └──────────┘   │
│ ┌──────────┐ ┌──────────┐   │
│ │ 合計 712  │ │ 会派 15   │   │
│ └──────────┘ └──────────┘   │
│                              │
│ ROSTER PREVIEW               │
│ ┌──────────────────────────┐ │
│ │ 逢沢 一郎                │ │
│ │ 衆 / 自民 / 岡山1区      │ │
│ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │
│ │ 青木 愛                  │ │
│ │ 参 / 立憲 / 比例         │ │
│ └──────────────────────────┘ │
│ [全議員を検索 →]              │
└──────────────────────────────┘
```

---

## PowerSemicircleGauge — 詳細仕様（新規追加）

```text
ゲージの構成要素（内側から外側）:

1. gauge-track arc  (180°, bg: gauge-track #1E2A40, stroke-width: 24px)
2. party arcs       (座席数に比例した弧、gauge-1〜8で色分け、clockwise)
3. majority marker  (50%位置に白い垂直ティック + ラベル)
4. center label     (ゲージ下部中央に「衆議院」「参議院」テキスト)

ゲージサイズ:
- Desktop: width 280px, arc radius 110px, stroke-width 28px
- Mobile:  width 240px, arc radius 90px,  stroke-width 22px

過半数マーカー:
- 位置: ゲージの真上中央（180°のうちの90°、12時位置）
- スタイル: 白い縦線 2px × 32px + 「過半数」ラベル (type-caption, text-primary)
- 色: gauge-majority (#FFFFFF)

凡例 (SeatLegend):
- ゲージ下部に配置
- Desktop: 横並び（最大4項目）、overflow は「他 N」でまとめる
- Mobile: 2カラムグリッド
- 各項目: ■ (12px, 対応gauge色) + 党名 (type-label) + 席数 (type-mono)

MajorityStatusPanel（ゲージ下部）:
- 「与党: XXX / 465 議席」→ text-primary
- 「過半数ライン: 233」 → text-secondary
- 「● 過半数到達: はい」 → lime accent (#A7F83B) + success fact bg
- 「● 過半数到達: いいえ」→ amber accent (#FFBE3D) + warning fact bg
```

---

## `/search` Search Results Page

Purpose: Make filtering and comparing results efficient.

### Desktop Wireframe（詳細版）

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ ウシガー                                           議員検索  このサイト      │
├──────────────────────────────────────────────────────────────────────────────┤
│  padding-top: space-6                                                        │
│                                                                              │
│  ┌──────────────────────────┐ ┌───────────────────────────────────────────┐  │
│  │ FILTER PANEL             │ │ SEARCH RESULTS                            │  │
│  │ (HudPanel, width: 240px) │ │ (flex-grow: 1)                            │  │
│  │                          │ │                                           │  │
│  │ 院                       │ │  CommandSearch (compact, inline)          │  │
│  │ [すべて][衆][参]          │ │  ┌───────────────────────────┐ [検索]     │  │
│  │                          │ │  │ 青木                       │           │  │
│  │ 政党・会派                │ │  └───────────────────────────┘           │  │
│  │ [select ▼]               │ │                                           │  │
│  │                          │ │  検索: "青木"  2件  (type-label, muted)  │  │
│  │ 選挙区                   │ │                                           │  │
│  │ [select ▼]               │ │  ┌───────────────────────────────────────┐ │  │
│  │                          │ │  │ RosterTable                           │ │  │
│  │ 区分                     │ │  │ 氏名          院   政党      選挙区    │ │  │
│  │ [すべて][小][比]          │ │  │ ─────────────────────────────────── │ │  │
│  │                          │ │  │ 青木 愛       参   立憲      比例      │ │  │
│  │ [条件をクリア]            │ │  │ 青木 一彦     参   自民      鳥取・島根│ │  │
│  └──────────────────────────┘ │  └───────────────────────────────────────┘ │  │
│                               │                                           │  │
│                               │  [前へ]  1 / 1  [次へ]                   │  │
│                               └───────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### RosterTable 行スタイル（新規追加）

```text
各行の構成:
  氏名 (type-subtitle, text-primary, 180px)
  院  (StatusChip: 衆 / 参, 50px)
  政党 (type-body, text-secondary, 140px)
  選挙区 (type-body, text-secondary, 130px)
  [詳細 →] (TextButton, text-right)

行の状態:
  Default: bg transparent, border-bottom: line-subtle 1px
  Hover:   bg bg-surface-raised, cursor pointer
  Focus:   border: accent-cyan 1px
```

### Mobile Wireframe（詳細版）

```text
┌──────────────────────────────┐
│ ウシガー              [☰]  │
├──────────────────────────────┤
│ ┌──────────────────────────┐ │
│ │ 青木                     │ │
│ └──────────────────────────┘ │
│ [フィルタ ▼]  [並び順 ▼]     │
│ 2件                          │
│                              │
│ RosterCard (1件目)            │
│ ┌──────────────────────────┐ │
│ │ 青木 愛                  │ │
│ │ あおき あい              │ │
│ │ [参] 立憲民主党 / 比例   │ │
│ │                  [詳細→] │ │
│ └──────────────────────────┘ │
│                              │
│ RosterCard (2件目)            │
│ ┌──────────────────────────┐ │
│ │ 青木 一彦                │ │
│ │ あおき かずひこ          │ │
│ │ [参] 自由民主党 / 鳥取・島根│
│ │                  [詳細→] │ │
│ └──────────────────────────┘ │
│                              │
│ [前へ] 1/1 [次へ]            │
└──────────────────────────────┘
```

### RosterCard スタイル（新規追加）

```text
背景: bg-surface-raised (#172033)
Border: 1px line-subtle (#243049)
Border-radius: 2px
Padding: space-4 (16px)
Gap between rows: space-2 (8px)

レイアウト:
Row 1: 氏名 (type-subtitle, text-primary) + よみがな (type-caption, text-muted)
Row 2: StatusChip(院) + 政党 (type-label, text-secondary) + 選挙区 (type-label, text-muted)
Row 3 (right-aligned): [詳細 →] TextButton (accent-cyan)

Hover: border-color → line-strong (#3D4D72)
```

---

## `/legislators/[id]` 議員詳細ページ

Purpose: Provide factual, source-linked information for one legislator.

### Desktop Wireframe（詳細版）

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ ウシガー                                           議員検索  このサイト      │
├──────────────────────────────────────────────────────────────────────────────┤
│  [← 検索結果に戻る]  (TextButton)                                            │
│  padding-top: space-6                                                        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ LegislatorProfileHeader                                                 │ │
│  │ (HudPanel, accent-cyan left-border 3px, padding: space-6)               │ │
│  │                                                                         │ │
│  │  逢沢 一郎  (type-display, text-primary)                                │ │
│  │  あいさわ いちろう  (type-body, text-muted)                             │ │
│  │  [衆議院]  [現職]  ← StatusChip x2                                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌──────────────────────────────────┐ ┌──────────────────────────────────┐  │
│  │ InfoPanel「基本情報」(HudPanel)   │ │ DataSourcePanel「データソース」   │  │
│  │                                  │ │ (HudPanel)                        │  │
│  │  院:       衆議院                │ │                                  │  │
│  │  会派:     自由民主党・無所属...  │ │  取得元:  衆議院公式サイト         │  │
│  │  選挙区:   岡山1区（小選挙区）   │ │  URL: [link]                     │  │
│  │  期種別:   general               │ │  取得日:  2026-05-04             │  │
│  │                                  │ │                                  │  │
│  └──────────────────────────────────┘ └──────────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ FutureModulePanel「今後追加予定のデータ」(HudPanel, dashed border)       │ │
│  │                                                                         │ │
│  │  [経歴]  [SNS・公式リンク]  [投票履歴]  [政策情報]                       │ │
│  │                                                                         │ │
│  │  このセクションのデータは現在収集中です。                                │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Wireframe（新規追加）

```text
┌──────────────────────────────┐
│ ウシガー              [☰]  │
├──────────────────────────────┤
│ [← 戻る]                     │
│                              │
│ LegislatorProfileHeader      │
│ ┌──────────────────────────┐ │
│ │ 逢沢 一郎                │ │
│ │ あいさわ いちろう        │ │
│ │ [衆議院]  [現職]         │ │
│ └──────────────────────────┘ │
│                              │
│ InfoPanel「基本情報」         │
│ ┌──────────────────────────┐ │
│ │ 院:   衆議院              │ │
│ │ 会派: 自民・無所属...     │ │
│ │ 選挙区: 岡山1区 (小)     │ │
│ └──────────────────────────┘ │
│                              │
│ DataSourcePanel              │
│ ┌──────────────────────────┐ │
│ │ 取得元: 衆議院公式サイト  │ │
│ │ 取得日: 2026-05-04       │ │
│ └──────────────────────────┘ │
│                              │
│ FutureModulePanel            │
│ ┌──────────────────────────┐ │
│ │ 今後追加予定のデータ      │ │
│ │ 経歴 / SNS / 投票 / 政策 │ │
│ └──────────────────────────┘ │
└──────────────────────────────┘
```

### InfoPanel フィールド定義（新規追加）

| フィールド名 | データソース | 型 | 表示形式 |
|---|---|---|---|
| 院 | `legislators.house` | string | 衆議院 / 参議院 |
| 現在の会派 | `parties.name` | string | テキスト |
| 選挙区 | `districts.name` | string | 例: 岡山1区（小選挙区） |
| 区分 | `districts.type` | string | 小選挙区 / 比例区 |
| ステータス | `legislators.status` | string | 現職 / 元議員 |

---

## Empty State & Loading（新規追加）

### EmptyState（検索結果0件）

```text
┌──────────────────────────────────────────────────────┐
│                                                      │
│           ○  (outline circle icon, text-muted)       │
│                                                      │
│           「XXX」に一致する議員が見つかりませんでした  │
│           (type-body, text-muted)                    │
│                                                      │
│           [条件をクリアして再検索]                    │
│           (PrimaryButton, accent-cyan)                │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### LoadingSkeleton

```text
RosterTable のローディング状態:

  ┌─────────────────────────────────────────────────────────┐
  │ ████████████  ██  ██████████  ████████   (opacity 0.15) │
  │ ████████████  ██  ██████████  ████████                  │
  │ ████████████  ██  ██████████  ████████                  │
  └─────────────────────────────────────────────────────────┘

  アニメーション: shimmer (background-position: left to right, 1.5s infinite)
  色: bg-surface-raised → bg-surface (gradient)
```

### FallbackData 表示状態

バックエンド未起動時（現在の実装がフォールバックデータを表示する状態）:

```text
Header右端 or ページ下部に:
  [⚠ オフラインデータ表示中]
  (type-caption, amber accent, warning fact bg)
```

---

## Component Inventory（拡張版）

### 変更・追加コンポーネント

| Component | v1からの変更 | 詳細 |
|---|---|---|
| `RosterCard` | 仕様追加 | よみがな行を追加、詳細ボタン位置を右下に固定 |
| `RosterTable` | 仕様追加 | hover/focusスタイル、行の列幅を明記 |
| `PowerSemicircleGauge` | 仕様追加 | サイズ・stroke・凡例レイアウト詳細化 |
| `InfoPanel` | 仕様追加 | フィールド定義と表示形式を追加 |
| `EmptyState` | 新規 | 0件時のビジュアル仕様 |
| `LoadingSkeleton` | 新規 | shimmerアニメーション仕様 |
| `FallbackBanner` | 新規 | フォールバックデータ表示時のバナー |

### コンポーネント一覧（変更なし）

元の`wireframes.md`の `## Component Inventory` セクションを参照。

---

## Top Page Power Map Section（補足）

Gauge UI notes（追記）:

- ゲージの弧はSVGの`stroke-dasharray` / `stroke-dashoffset`で実装を推奨
- 過半数マーカーは常に表示（ホバー不要）
- セグメントホバー時は `GaugeTooltip` を表示: 党名 + 議席数 + 全体%
- 読み込み中はグレーの全弧を表示し、データロード後にアニメーションで展開

Neutrality notes（変更なし）:
- Label "過半数到達" instead of "勝利" or "支配"
- Use factual grouping rules and document them
- Do not place ruling parties visually "above" opposition; order by seat count

---

## Figma Component Mapping（新規追加）

現在のFigmaファイル（`Civic Strategy HUD` ページ）と本ドキュメントのコンポーネントの対応:

| このドキュメントのコンポーネント | Figmaのフレーム名 |
|---|---|
| `SiteHeader` | `Component Library / SiteHeader` |
| `HudPanel` | `Component Library / HudPanel` |
| `CommandSearch` | `Component Library / CommandSearch` |
| `PowerSemicircleGauge` | `Component Library / PowerSemicircleGauge` |
| `RosterTable` | `Component Library / RosterTable` |
| `RosterCard` | `Component Library / RosterCard` |
| `StatsCounter` | `Component Library / StatsCounter` |
| `StatusChip` | `Component Library / StatusChip` |
| Top Page全体 | `Screen Preview / Top Page` |
| 検索結果ページ全体 | `Screen Preview / Search Results` |
| 議員詳細ページ全体 | `Screen Preview / Legislator Detail` |

---

## 改良の優先順位（新規追加）

Figmaのアップデート優先順位:

1. **PowerSemicircleGauge** — 仕様が最も具体化されたため、Figmaの実装精度を上げる
2. **RosterCard** — よみがな行の追加・詳細ボタン位置の修正
3. **RosterTable** — hover/focusスタイルの追加
4. **LegislatorProfileHeader** — accent-cyan left-borderの実装
5. **EmptyState** — 新規コンポーネントとして追加
6. **LoadingSkeleton** — shimmer仕様の反映
7. **FallbackBanner** — オフライン状態のバナー追加
