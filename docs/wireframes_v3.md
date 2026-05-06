# Web Wireframes v3

> **このファイルについて**: `docs/wireframes_v2.md` の評価結果とユーザーコメントを反映した版。
> v1/v2は残し、本ファイルを次の実装・Figma更新の基準とする。

---

## v3で反映した主な変更

- ブランド名を `ウシガー` に確定。
- Top Page の `COMMAND SEARCH` 表記を `政治家を探す` に変更。
- Top Page の `QUICK FILTERS` を検索ボックス右側へ移動し、名称を `クイック検索` に変更。
- Power Map の党派並び順を「与党第1党、与党第2党、野党第1党…」に変更。
- 2026年5月現在の与党区分を確認し、自由民主党・日本維新の会を与党として扱う。
- Top Page の `ROSTER PREVIEW` を `注目の大型新人議員` に変更し、当選1期目の注目議員枠として再定義。
- v2評価で指摘した、ゲージ数値の定義、API未対応項目、Figma対応表の扱いを明記。

---

## Brand Name

Top Page左上の `ウシガー` は説明的すぎるため、短く発音しやすいサービス名へ変更する。
名称は `ウシガー` に確定。Figma / SPAではこの名称を使う。

| Name | 読み | 意図 | メモ |
|---|---|---|---|
| `ウシガー` | ウシガー | 口に出しやすく、少し不思議で覚えやすい響き | 採用名称。短く、ゲーム/アプリ的な軽さがある。 |

ヘッダー表示:

```text
[ウシガー]
```

運用上の注意:

- 政党・思想・勝敗を連想させる副題は付けない。
- 必要に応じて補助コピーで「政治家検索」または「国会議員データベース」と説明する。

---

## Design Direction

Working concept: **Civic Strategy HUD**

The site should feel like a strategy game's command interface while remaining a neutral public-information tool. Use game-like panels, gauges, tabs, filters, and dense roster layouts. Do not use rankings, power scores, attack/defense language, or visual treatment that implies one party or legislator is better than another.

Core pages:

- `/` - 議員検索・一覧ページ
- `/search` - 検索結果ページ
- `/legislators/[id]` - `〇〇 衆議院議員` / `〇〇 参議院議員`

Removed page:

- `/power-map` - 独立ページは作らない。勢力図はTop Pageに統合する。

---

## External Political Alignment Baseline

2026年5月現在のワイヤーでは、以下を与党として扱う。

| Alignment | Party | Reason |
|---|---|---|
| 与党第1党 | 自由民主党 | 高市内閣の連立政権中核。 |
| 与党第2党 | 日本維新の会 | 自由民主党との連立政権合意に基づく与党。 |
| 野党 | その他の政党・会派 | 上記2党以外。 |

確認根拠:

- 首相官邸の令和8年1月23日政府声明に、高市内閣は「自由民主党と日本維新の会との間の『連立政権合意書』を礎とする連立政権」と記載。
- 追加確認として、LDP-JIP coalitionの公開情報でも自由民主党・日本維新の会の連立が示されている。

実装メモ:

- Supabase `public.parties` に `alignment` 系カラムを追加済み。
- 追加済みカラム: `alignment`, `alignment_rank`, `alignment_rank_member_count`, `alignment_basis`, `alignment_source_url`, `alignment_source_checked_at`。
- `alignment` は外部ソースに基づく政権枠組みから設定する。
- `alignment_rank` は `active_legislators` の所属議員数から定量的に導出する。
- 詳細は `docs/party-alignment.md` を参照。

---

## Data Rules For Power Map

ゲージ数値は混乱しやすいため、v3では以下を明確化する。

### Seat Count Basis

| Display | Basis | Notes |
|---|---|---|
| 議員検索・一覧件数 | DB上の現職レコード数 | 現在: 衆議院465、参議院247。 |
| Power Mapの議席総数 | 原則としてDB上の現員数 | 欠員・定数差異を避け、現データと一致させる。 |
| 過半数ライン | `floor(totalSeats / 2) + 1` | 衆議院465なら233、参議院247なら124。 |
| 定数ベース表示 | 将来のオプション | 参議院248など定数ベースを使う場合は「定数ベース」と明記する。 |

### Party Ordering

各院のPower Mapは、左から以下の順に並べる。

1. 与党第1党: 自由民主党
2. 与党第2党: 日本維新の会
3. 野党第1党: 野党のうち議席数が最多の政党・会派
4. 野党第2党以降: 議席数降順
5. 無所属・その他: 最後

中立性ルール:

- 与党を左に置くのは政権構成を説明するためであり、優劣表現ではない。
- ラベルは `与党第1党` / `与党第2党` / `野党第1党` のように事実ベースにする。
- `勝利`, `支配`, `制圧`, `陣営勝ち` などの言葉は使わない。

---

## Typography Tokens

| Token | Size | Weight | Line Height | Usage |
|---|---|---|---|---|
| `type-display` | 28px | 700 | 1.2 | ページ見出し |
| `type-title` | 20px | 600 | 1.3 | パネル見出し・議員氏名 |
| `type-subtitle` | 16px | 600 | 1.4 | カード見出し |
| `type-body` | 14px | 400 | 1.6 | 本文・説明 |
| `type-label` | 12px | 500 | 1.4 | ラベル・チップ |
| `type-mono` | 13px | 400 | 1.5 | 数値・ID・カウンター |
| `type-caption` | 11px | 400 | 1.4 | 補足・出典 |

フォント:

- Japanese/UI: `'Noto Sans JP', 'Inter', sans-serif`
- Numeric HUD: `'JetBrains Mono', 'Fira Code', monospace`

---

## Spacing Tokens

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

Border radius:

- HUD panels and cards: `2px`
- Chips: `999px`
- Inputs/buttons: `4px`

Focus/active glow:

- `0 0 0 1px var(--accent-cyan)`

---

## Color Palette

元の `docs/wireframes.md` の `## Color Palette` を継承する。

追加ルール:

1. ページ背景は必ず `bg-canvas (#070A12)`。
2. カード・パネルは `bg-surface (#101622)` または `bg-surface-raised (#172033)`。
3. インタラクティブ要素のフォーカスリングは `accent-cyan (#38D5FF)`。
4. ゲージカラーは公式政党カラーではなく、中立カテゴリ色として使う。
5. 与党・野党を色相で優劣づけしない。並び順とラベルだけで区分する。

---

## Shared Layout

### Desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ SITE HUD BAR  height: 56px                                                   │
│ [ウシガー]                                       [議員検索] [このサイトについて] │
├──────────────────────────────────────────────────────────────────────────────┤
│ PAGE CONTENT  max-width: 1200px                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Header behavior:

- `ウシガー` を正式なサービス名として表示する。
- Site name links to `/`。
- Active nav item: bottom border 2px `accent-cyan`。
- Avoid party-colored global navigation。

### Mobile

```text
┌──────────────────────────────┐
│ [ウシガー]                 [☰]  │
├──────────────────────────────┤
│ PAGE CONTENT                 │
└──────────────────────────────┘
```

---

## `/` Top Page

Purpose: Let users immediately search the legislator database and understand the current power composition.

### Desktop Wireframe

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ ウシガー                                                議員検索  このサイト      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TOP CONTROL ROW                                                              │
│  ┌──────────────────────────────────────────────────┐ ┌────────────────────┐ │
│  │ 政治家を探す                                      │ │ クイック検索        │ │
│  │ ┌────────────────────────────────┐ ┌───────────┐ │ │ 院                 │ │
│  │ │ 氏名・よみ・政党・選挙区で検索 │ │ 検索      │ │ │ [すべて][衆][参]   │ │
│  │ └────────────────────────────────┘ └───────────┘ │ │ 政党・会派 [select] │ │
│  │ [すべて] [衆議院] [参議院]                         │ │ 選挙区     [select] │ │
│  └──────────────────────────────────────────────────┘ │ [条件をクリア]      │ │
│                                                        └────────────────────┘ │
│                                                                              │
│  POWER MAP STRIP                                                              │
│  ┌──────────────────────────────────────┐ ┌────────────────────────────────┐ │
│  │ 衆議院 勢力図                         │ │ 参議院 勢力図                   │ │
│  │                                      │ │                                │ │
│  │  左から:                             │ │ 左から:                         │ │
│  │  与党1 自民 → 与党2 維新 → 野党1...   │ │ 与党1 自民 → 与党2 維新 → 野党1...│ │
│  │                                      │ │                                │ │
│  │       ╭────────────────────╮         │ │      ╭────────────────────╮    │ │
│  │      ╱ party arcs by order  ╲        │ │     ╱ party arcs by order  ╲   │ │
│  │     ╱________________________╲       │ │    ╱________________________╲  │ │
│  │              │ 過半数ライン           │ │             │ 過半数ライン       │ │
│  │                                      │ │                                │ │
│  │  与党: 自民+維新 / 現員465            │ │ 与党: 自民+維新 / 現員247        │ │
│  │  過半数ライン: 233                    │ │ 過半数ライン: 124                │ │
│  │  ● 過半数到達: はい                   │ │ ● 過半数到達: いいえ/はい        │ │
│  │  凡例: 与党1 自民 / 与党2 維新 / 野党1...│ │ 凡例: 与党1 自民 / 与党2 維新... │ │
│  └──────────────────────────────────────┘ └────────────────────────────────┘ │
│                                                                              │
│  STATS COUNTER GRID                                                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐                 │
│  │ 衆議院 465  │ │ 参議院 247  │ │ 合計 712    │ │ 政党・会派15│                 │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘                 │
│                                                                              │
│  注目の大型新人議員                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ 当選1期目の新人議員から、話題性・代表性・新規性の観点で注目枠を掲載       │  │
│  │ ただし「優秀」「有力」「格上」などの評価語は使わない                      │  │
│  │                                                                        │  │
│  │  氏名          院   政党・会派        選挙区        注目理由             │  │
│  │  新人 A        衆   自民              ○○区          初当選 / 若手       │  │
│  │  新人 B        衆   チームみらい      比例          新党から初当選       │  │
│  │  新人 C        参   参政党            ○○県          初当選 / 新勢力     │  │
│  │                                                        [一覧を見る →]    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Wireframe

```text
┌──────────────────────────────┐
│ ウシガー                   [☰]  │
├──────────────────────────────┤
│ 政治家を探す                 │
│ ┌──────────────────────────┐ │
│ │ 氏名・よみ・政党・選挙区 │ │
│ └──────────────────────────┘ │
│ [すべて] [衆] [参]           │
│ [検索 ─────────────────────] │
│                              │
│ クイック検索                 │
│ ┌──────────────────────────┐ │
│ │ 院 / 政党・会派 / 選挙区 │ │
│ └──────────────────────────┘ │
│                              │
│ 衆議院 勢力図                 │
│ ┌──────────────────────────┐ │
│ │ 与党1→与党2→野党1→...    │ │
│ │ 半円ゲージ                │ │
│ │ 与党: 自民+維新           │ │
│ │ 過半数ライン: 233         │ │
│ └──────────────────────────┘ │
│                              │
│ 参議院 勢力図                 │
│ ┌──────────────────────────┐ │
│ │ 与党1→与党2→野党1→...    │ │
│ │ 半円ゲージ                │ │
│ │ 与党: 自民+維新           │ │
│ │ 過半数ライン: 124         │ │
│ └──────────────────────────┘ │
│                              │
│ 注目の大型新人議員                 │
│ ┌──────────────────────────┐ │
│ │ 新人 A                   │ │
│ │ 衆 / 政党 / 選挙区       │ │
│ │ 注目理由                 │ │
│ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │
│ │ 新人 B                   │ │
│ │ 参 / 政党 / 選挙区       │ │
│ │ 注目理由                 │ │
│ └──────────────────────────┘ │
└──────────────────────────────┘
```

---

## Top Page Components

### SearchPanel

Former name:

- `CommandSearch`

Display label:

- `政治家を探す`

Responsibilities:

- keyword input
- submit action
- house segmented control
- pass filters to `/search`

### QuickSearchPanel

Former name:

- `Quick Filters`

Display label:

- `クイック検索`

Placement:

- Desktop: right side of `政治家を探す`
- Mobile: immediately below `政治家を探す`

Fields:

- 院
- 政党・会派
- 選挙区
- 区分
- 条件クリア

### FeaturedFreshmenPanel

Former name:

- `Roster Preview`

Display label:

- `注目の大型新人議員`

Definition:

- 当選1期目の新人議員から、ユーザーが探索したくなる代表例を掲載する枠。
- 「大型」はUI上の見出しとして使うが、個々の議員を優劣評価しない。

Candidate selection rules:

1. `election_count = 1` または同等の「当選1期目」判定があること。
2. 複数政党・複数院・複数選挙区から偏りなく選ぶ。
3. 注目理由は事実に限定する。
4. 例: `初当選`, `新党から当選`, `最年少級`, `比例上位`, `地方首長経験`, `専門職出身`。
5. `将来有望`, `エース`, `スター`, `強い`, `弱い` など評価語は禁止。

Current data gap:

- 現APIには `election_count`, `age`, `previous_role`, `first_elected_at` がない。
- 初期実装ではプレースホルダー、または手動キュレーションJSONで表示する。
- 本実装では `legislator_terms` から当選回数を集計するAPI追加が望ましい。

---

## PowerSemicircleGauge

### Detailed Spec

```text
ゲージ構成:

1. gauge-track arc
2. party arcs
3. majority marker
4. chamber label
5. majority status
6. legend
```

Visual size:

- Desktop: width 280px, arc radius 110px, stroke-width 28px
- Mobile: width 240px, arc radius 90px, stroke-width 22px

Ordering:

- 与党第1党 → 与党第2党 → 野党第1党 → 野党第2党 → ... → その他

Recommended implementation:

- SVG path is acceptable for the current SPA.
- If animation is added, use `stroke-dasharray` / `stroke-dashoffset`.
- Tooltip on hover/focus: party/group name, alignment label, seats, percentage.

State labels:

- `過半数到達: はい`
- `過半数到達: いいえ`
- No `勝利`, `敗北`, `支配`, `制圧` labels.

---

## `/search` Search Results Page

Purpose: Make filtering and comparing results efficient.

### Desktop Wireframe

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ ウシガー                                                議員検索  このサイト      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────┐ ┌───────────────────────────────────────────┐  │
│  │ FILTER PANEL             │ │ SEARCH RESULTS                            │  │
│  │                          │ │                                           │  │
│  │ 院                       │ │ 政治家を探す compact                     │  │
│  │ [すべて][衆][参]          │ │ ┌───────────────────────────┐ [検索]     │  │
│  │ 政党・会派 [select]       │ │ │ 青木                       │           │  │
│  │ 選挙区     [select]       │ │ └───────────────────────────┘           │  │
│  │ 区分       [小][比]       │ │                                           │  │
│  │ [条件をクリア]            │ │ 検索: "青木" 2件                         │  │
│  │                          │ │                                           │  │
│  └──────────────────────────┘ │ RosterTable                               │  │
│                               │ 氏名 / よみ / 院 / 政党 / 選挙区 / 詳細    │  │
│                               └───────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### RosterTable

Rows:

- 氏名
- よみがな
- 院
- 政党・会派
- 選挙区
- 詳細

States:

- Default: transparent row with bottom border
- Hover: `bg-surface-raised`
- Focus: `accent-cyan` outline

### Mobile

Use `RosterCard` instead of dense table.

RosterCard layout:

1. 氏名
2. よみがな
3. `[衆/参] 政党・会派 / 選挙区`
4. right-aligned `詳細 →`

---

## `/legislators/[id]` Legislator Detail Page

Purpose: Provide factual, source-linked information for one legislator.

### Desktop Wireframe

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ ウシガー                                                議員検索  このサイト      │
├──────────────────────────────────────────────────────────────────────────────┤
│ [← 検索結果に戻る]                                                            │
│                                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐  │
│ │ LegislatorProfileHeader  left-border: accent-cyan 3px                   │  │
│ │ 逢沢 一郎                                                               │  │
│ │ あいさわ いちろう                                                       │  │
│ │ [衆議院] [現職]                                                         │  │
│ └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌──────────────────────────────────┐ ┌──────────────────────────────────┐   │
│ │ InfoPanel 基本情報                │ │ DataSourcePanel データソース      │   │
│ │ 院: 衆議院                        │ │ 取得元: 衆議院公式サイト          │   │
│ │ 会派: 自由民主党                  │ │ URL: API追加後に表示              │   │
│ │ 選挙区: 岡山1区                   │ │ 取得日: API追加後に表示           │   │
│ │ 区分: 小選挙区                    │ │                                  │   │
│ └──────────────────────────────────┘ └──────────────────────────────────┘   │
│                                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐  │
│ │ FutureModulePanel 今後追加予定のデータ                                  │  │
│ │ [経歴] [SNS・公式リンク] [投票履歴] [政策情報]                           │  │
│ │ このセクションのデータは現在収集中です。                                  │  │
│ └─────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

API gap notes:

- `status` is not currently returned by `/v1/legislators`.
- `source_url` and `retrieved_at` are not currently returned by `/v1/legislators`.
- Detail page may show placeholders until API/model expansion.

Recommended API additions:

- `status`
- `source_url`
- `source_name`
- `retrieved_at`
- `term_count` or `election_count`

---

## Empty State & Loading

### EmptyState

```text
┌──────────────────────────────────────────────────────┐
│                                                      │
│           ○                                          │
│           「XXX」に一致する議員が見つかりませんでした │
│           [条件をクリアして再検索]                    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### LoadingSkeleton

- Use shimmer animation.
- Preserve final row/card dimensions to avoid layout shift.

### FallbackBanner

Use when backend is unreachable and SPA fallback data is shown.

```text
[オフラインデータ表示中]
```

Placement:

- Desktop: header right edge or top of page content.
- Mobile: below header.

Tone:

- Amber warning state.
- Do not imply data is wrong; say it is fallback/offline sample data.

---

## Figma Component Mapping

Important:

- The table below is the **target naming convention**, not a verified list of existing Figma nodes.
- Figma MCP call limit prevented a fresh full node-name verification during this pass.
- Before Figma update, inspect existing frames or regenerate them from `scripts/figma/create_civic_strategy_hud.js`.

| Component | Target Figma frame name |
|---|---|
| Brand/header | `Component Library / SiteHeader` |
| Search panel | `Component Library / SearchPanel` |
| Quick search | `Component Library / QuickSearchPanel` |
| Power gauge | `Component Library / PowerSemicircleGauge` |
| Featured freshmen | `Component Library / FeaturedFreshmenPanel` |
| Roster table | `Component Library / RosterTable` |
| Roster card | `Component Library / RosterCard` |
| Detail profile | `Component Library / LegislatorProfileHeader` |
| Empty state | `Component Library / EmptyState` |
| Loading | `Component Library / LoadingSkeleton` |
| Fallback | `Component Library / FallbackBanner` |

---

## Implementation Priority

1. Update SPA header brand to `ウシガー`.
2. Rename Top Page `COMMAND SEARCH` label to `政治家を探す`.
3. Move `クイック検索` to the right side of search on desktop.
4. Reorder Power Map segments by alignment: LDP → JIP → opposition parties by seat count.
5. Rename `ROSTER PREVIEW` to `注目の大型新人議員` and switch content model to first-term notable legislators.
6. Add `FallbackBanner`.
7. Add `RosterCard` kana row and better mobile cards.
8. Add detail page `FutureModulePanel`.
9. Add stats endpoint/API model work for real gauge and first-term data.

---

## Open Decisions

- Brand name is fixed as `ウシガー`.
- Whether Power Map should use DB current member count or legal chamber capacity in public copy.
- Whether to move party alignment into a separate history table later.
- Criteria and editorial policy for `注目の大型新人議員`.
