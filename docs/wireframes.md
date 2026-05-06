# Web Wireframes

## Design Direction

Working concept: **Civic Strategy HUD**

The site should feel like a strategy game's command interface while remaining a neutral public-information tool. Use game-like panels, gauges, tabs, filters, and dense roster layouts. Do not use rankings, power scores, attack/defense language, or visual treatment that implies one party or legislator is better than another.

Core pages:

- `/` - 議員検索・一覧ページ
- `/search` - 検索結果ページ
- `/legislators/[id]` - `〇〇 衆議院議員` / `〇〇 参議院議員`

## Shared Layout

### Desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ SITE HUD BAR                                                                 │
│ [ウシガー]                               [議員検索] [このサイトについて] │
├──────────────────────────────────────────────────────────────────────────────┤
│ PAGE CONTENT                                                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

Shared header behavior:

- Site name links to `/`.
- Active nav item uses a subtle illuminated underline.
- Avoid party-colored global navigation.
- Keep labels utilitarian and neutral.

### Mobile

```text
┌──────────────────────────────┐
│ [ウシガー]            [☰]  │
├──────────────────────────────┤
│ PAGE CONTENT                 │
└──────────────────────────────┘
```

Mobile behavior:

- Collapse navigation into a menu.
- Keep search access one tap away from every page.
- Filters open in a bottom sheet or full-width drawer.

## `/` Top Page

Purpose: Let users immediately search the legislator database.

### Desktop Wireframe

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ ウシガー                                           議員検索  このサイト      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ COMMAND SEARCH                                                        │  │
│  │ ┌────────────────────────────────────────────────────┐ [検索]          │  │
│  │ │ 氏名・よみ・政党・選挙区で検索                    │                 │  │
│  │ └────────────────────────────────────────────────────┘                 │  │
│  │ [すべて] [衆議院] [参議院]                                             │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────┐ ┌────────────────────────────────┐ │
│  │ 衆議院 勢力図                         │ │ 参議院 勢力図                   │ │
│  │                                      │ │                                │ │
│  │          過半数ライン                 │ │        過半数ライン             │ │
│  │               │                      │ │             │                  │ │
│  │       ╭───────┴───────╮              │ │     ╭───────┴───────╮          │ │
│  │    ╭──╯ party arcs     ╰──╮           │ │  ╭──╯ party arcs     ╰──╮       │ │
│  │   ╰──────────────────────╯           │ │ ╰──────────────────────╯       │ │
│  │  与党 xxx / 過半数 xxx                │ │ 与党 xxx / 過半数 xxx           │ │
│  └──────────────────────────────────────┘ └────────────────────────────────┘ │
│                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐                 │
│  │ 衆議院      │ │ 参議院      │ │ 合計        │ │ 政党・会派  │                 │
│  │ 465        │ │ 247        │ │ 712        │ │ 15         │                 │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘                 │
│                                                                              │
│  ┌──────────────────────────────┐ ┌───────────────────────────────────────┐  │
│  │ QUICK FILTERS                 │ │ ROSTER PREVIEW                        │  │
│  │ 院                            │ │ 氏名        院     政党       選挙区    │  │
│  │ 政党・会派                    │ │ 逢沢 一郎   衆     自民       岡山1     │  │
│  │ 選挙区                        │ │ 青木 愛     参     立憲       比例      │  │
│  │ 区分                          │ │ ...                                    │  │
│  └──────────────────────────────┘ └───────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Wireframe

```text
┌──────────────────────────────┐
│ ウシガー              [☰]  │
├──────────────────────────────┤
│ COMMAND SEARCH               │
│ ┌──────────────────────────┐ │
│ │ 氏名・よみ・政党・選挙区 │ │
│ └──────────────────────────┘ │
│ [すべて] [衆] [参]           │
│ [検索]                       │
│                              │
│ 衆議院 勢力図                 │
│ ┌──────────────────────────┐ │
│ │      半円ゲージ           │ │
│ │  与党 xxx / 過半数 xxx    │ │
│ └──────────────────────────┘ │
│ 参議院 勢力図                 │
│ ┌──────────────────────────┐ │
│ │      半円ゲージ           │ │
│ │  与党 xxx / 過半数 xxx    │ │
│ └──────────────────────────┘ │
│                              │
│ ┌──────┐ ┌──────┐            │
│ │衆465 │ │参247 │            │
│ └──────┘ └──────┘            │
│ ┌──────┐ ┌──────┐            │
│ │合計712│ │会派15│            │
│ └──────┘ └──────┘            │
│                              │
│ ROSTER PREVIEW               │
│ ┌──────────────────────────┐ │
│ │ 逢沢 一郎                │ │
│ │ 衆議院 / 自民 / 岡山1     │ │
│ └──────────────────────────┘ │
└──────────────────────────────┘
```

Game UI notes:

- Search area can look like a command console.
- Statistics can look like compact HUD counters.
- Roster preview can use a "unit list" treatment.

Neutrality notes:

- Default ordering is kana order.
- No party gets larger typography, stronger glow, or special placement.

## `/search` Search Results Page

Purpose: Make filtering and comparing results efficient.

### Desktop Wireframe

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ ウシガー                                           議員検索  このサイト      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────┐ ┌───────────────────────────────────────────┐  │
│  │ FILTER PANEL             │ │ SEARCH RESULTS                            │  │
│  │                          │ │ ┌───────────────────────────────────────┐ │  │
│  │ 院                       │ │ │ 検索: "青木"  2件                    │ │  │
│  │ [すべて][衆][参]          │ │ └───────────────────────────────────────┘ │  │
│  │                          │ │                                           │  │
│  │ 政党・会派                │ │ ┌───────────────────────────────────────┐ │  │
│  │ [select]                 │ │ │ 青木 愛                               │ │  │
│  │                          │ │ │ 参議院 / 立憲民主党 / 比例             │ │  │
│  │ 選挙区                   │ │ │ [詳細]                                │ │  │
│  │ [select]                 │ │ └───────────────────────────────────────┘ │  │
│  │                          │ │ ┌───────────────────────────────────────┐ │  │
│  │ 区分                     │ │ │ 青木 一彦                             │ │  │
│  │ [すべて][小][比]          │ │ │ 参議院 / 自由民主党 / 鳥取・島根       │ │  │
│  │                          │ │ │ [詳細]                                │ │  │
│  │ [条件をクリア]            │ │ └───────────────────────────────────────┘ │  │
│  └──────────────────────────┘ │                                           │  │
│                               │ [前へ] 1 / n [次へ]                       │  │
│                               └───────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Wireframe

```text
┌──────────────────────────────┐
│ ウシガー              [☰]  │
├──────────────────────────────┤
│ ┌──────────────────────────┐ │
│ │ 青木                     │ │
│ └──────────────────────────┘ │
│ [フィルタ] [並び順]          │
│ 2件                          │
│                              │
│ ┌──────────────────────────┐ │
│ │ 青木 愛                  │ │
│ │ 参議院 / 立憲民主党      │ │
│ │ 比例                     │ │
│ │ [詳細]                   │ │
│ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │
│ │ 青木 一彦                │ │
│ │ 参議院 / 自由民主党      │ │
│ │ 鳥取・島根               │ │
│ │ [詳細]                   │ │
│ └──────────────────────────┘ │
└──────────────────────────────┘
```

Game UI notes:

- Filter panel can feel like a loadout/filter console.
- Result items can be compact roster cards.
- Use icons for house, district type, and detail action where possible.

Neutrality notes:

- Use equal card sizing.
- Avoid "rare", "elite", "boss", "power" labels for legislators.

## `/legislators/[id]` Legislator Detail Page

Purpose: Show one legislator's factual profile.

Page title format:

- `{name} 衆議院議員`
- `{name} 参議院議員`

### Desktop Wireframe

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ ウシガー                                           議員検索  このサイト      │
├──────────────────────────────────────────────────────────────────────────────┤
│ [← 検索結果へ戻る]                                                            │
│                                                                              │
│ ┌──────────────────────────────────────┐ ┌────────────────────────────────┐ │
│ │ PROFILE HEADER                       │ │ DATA SOURCE                    │ │
│ │ 逢沢 一郎 衆議院議員                 │ │ 出典                           │ │
│ │ あいさわ いちろう                    │ │ 衆議院公式サイト               │ │
│ │ [現職] [衆議院]                      │ │ 最終取得日時                   │ │
│ └──────────────────────────────────────┘ └────────────────────────────────┘ │
│                                                                              │
│ ┌────────────────────────────────────────────────────────────────────────┐  │
│ │ BASIC DATA                                                             │  │
│ │ 所属政党・会派      自由民主党                                          │  │
│ │ 選挙区              岡山1                                               │  │
│ │ 区分                小選挙区                                            │  │
│ │ 選挙年              2024                                                │  │
│ │ 任期                2024-10-27 - 2028-10-26                              │  │
│ └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│ ┌────────────────────────────────────────────────────────────────────────┐  │
│ │ FUTURE MODULES                                                          │  │
│ │ 経歴 / 公式サイト・SNS / 投票履歴 / 政策・公約                          │  │
│ └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Wireframe

```text
┌──────────────────────────────┐
│ ウシガー              [☰]  │
├──────────────────────────────┤
│ [← 戻る]                      │
│ 逢沢 一郎 衆議院議員          │
│ あいさわ いちろう             │
│ [現職] [衆議院]               │
│                              │
│ BASIC DATA                   │
│ 所属  自由民主党              │
│ 選挙区 岡山1                  │
│ 区分  小選挙区                │
│ 選挙年 2024                  │
│                              │
│ DATA SOURCE                  │
│ 衆議院公式サイト              │
└──────────────────────────────┘
```

Game UI notes:

- Profile can resemble a character detail screen.
- Use structured data panels, not ranking meters.
- "Status" means active/inactive only.

Neutrality notes:

- No portrait art, faction icons, or symbolic imagery implying ideology.
- Official links only.

## Top Page Power Map Section

Purpose: Make chamber composition and majority status visible immediately after search.

Placement:

- Directly below the command search box.
- Show two semicircle gauges side by side on desktop.
- Stack 衆議院 then 参議院 on mobile.

Gauge contents:

- Chamber label: 衆議院 / 参議院
- Semicircle seat gauge
- Party arcs by seat count
- Majority marker
- 与党議席数
- 非与党・その他議席数
- 過半数ライン
- 過半数到達: はい / いいえ

Game UI notes:

- The gauges should be the most game-like element on the top page.
- They can feel like tactical control meters or territory gauges.
- Use subtle loading and hover motion, not celebration effects.

Neutrality notes:

- Label "過半数到達" instead of "勝利" or "支配".
- Use factual grouping rules and document them.
- Do not place ruling parties visually "above" opposition by default; order by seat count or a documented rule.

## Color Palette

Palette concept: **dark tactical interface + restrained neon signals**. The site should feel closer to a modern online strategy game dashboard than a government site, while keeping public data readable and politically neutral.

### Core Colors

| Token | Hex | Usage |
| --- | --- | --- |
| `bg-canvas` | `#070A12` | Full page background |
| `bg-surface` | `#101622` | Main panels, header, dense sections |
| `bg-surface-raised` | `#172033` | Cards, filter blocks, active table rows |
| `bg-command` | `#0B1020` | Search console and input-heavy areas |
| `line-subtle` | `#243049` | Panel borders and dividers |
| `line-strong` | `#3D4D72` | Active outlines, gauge track edges |
| `text-primary` | `#F2F6FF` | Main text |
| `text-secondary` | `#AAB8D8` | Metadata and secondary labels |
| `text-muted` | `#6F7E9E` | Disabled text, empty states |
| `accent-cyan` | `#38D5FF` | Primary action, active focus, HUD glow |
| `accent-lime` | `#A7F83B` | Positive factual status, loaded indicator |
| `accent-amber` | `#FFBE3D` | Caution, majority marker, pending states |
| `accent-rose` | `#FF4F7B` | Error and destructive feedback only |
| `neutral-white` | `#FFFFFF` | Tiny high-contrast marks, gauge ticks |

### Gauge Segment Colors

Use these as neutral categorical colors for semicircle gauge arcs. They are not official party colors and should be assigned by documented order, ideally seat count descending within each chamber.

| Token | Hex | Notes |
| --- | --- | --- |
| `gauge-1` | `#38D5FF` | Bright cyan |
| `gauge-2` | `#A7F83B` | Electric lime |
| `gauge-3` | `#FFBE3D` | Amber |
| `gauge-4` | `#B985FF` | Violet |
| `gauge-5` | `#FF6B45` | Coral |
| `gauge-6` | `#35E0A1` | Mint |
| `gauge-7` | `#6F8CFF` | Blue |
| `gauge-8` | `#F36BCE` | Magenta |
| `gauge-other` | `#65708A` | Other, independent, very small groups |
| `gauge-track` | `#1E2A40` | Empty arc track |
| `gauge-majority` | `#FFFFFF` | Majority line and tick |

### State Colors

| State | Background | Text / Icon | Border |
| --- | --- | --- | --- |
| Default chip | `#172033` | `#AAB8D8` | `#243049` |
| Active chip | `#102B3A` | `#F2F6FF` | `#38D5FF` |
| Success fact | `#182B1F` | `#A7F83B` | `#315D2A` |
| Warning fact | `#2B2413` | `#FFBE3D` | `#6D5320` |
| Error | `#321622` | `#FF9AB2` | `#FF4F7B` |
| Disabled | `#111827` | `#6F7E9E` | `#1D2738` |

### Visual Rules

- Use cyan as the main interactive color; reserve lime and amber for factual status.
- Do not make the whole UI blue or purple. Use color sparingly against dark neutral surfaces.
- Avoid official party-color mapping until the product has a clear documented policy.
- Glow should be subtle: border glow or text-shadow on active controls only.
- All text must meet practical contrast against its background, especially Japanese labels.

## Component Inventory

### Layout Components

| Component | Used On | Responsibility |
| --- | --- | --- |
| `AppShell` | All pages | Page background, width constraints, shared spacing |
| `SiteHeader` | All pages | Logo, primary navigation, mobile menu |
| `PageFrame` | All pages | Consistent content container and vertical rhythm |
| `HudPanel` | All pages | Reusable dark bordered panel with title slot |
| `SectionHeading` | All pages | Compact section titles and optional metadata |

### Search And Filter Components

| Component | Used On | Responsibility |
| --- | --- | --- |
| `CommandSearch` | Top, Search | Main keyword input, submit action, house tabs |
| `HouseSegmentedControl` | Top, Search | `すべて` / `衆議院` / `参議院` toggle |
| `FilterPanel` | Top, Search | Party, district, district type filters |
| `FilterDrawer` | Search mobile | Mobile filter bottom sheet or drawer |
| `SelectField` | Search | Styled select for party and district |
| `ClearFiltersButton` | Search | Reset filters to default state |

### Roster Components

| Component | Used On | Responsibility |
| --- | --- | --- |
| `RosterPreview` | Top | Small sample list from the legislator API |
| `RosterCard` | Top mobile, Search mobile | Legislator summary with detail action |
| `RosterTable` | Top desktop, Search desktop | Dense sortable-looking list without implying ranking |
| `LegislatorMetaLine` | Cards, Detail | House, party, district compact metadata |
| `PaginationControls` | Search | Previous/next paging and result position |
| `EmptyState` | Search | No-result guidance without heavy illustration |
| `LoadingSkeleton` | Search, Top | Stable loading rows and cards |

### Power Map Components

| Component | Used On | Responsibility |
| --- | --- | --- |
| `PowerMapStrip` | Top | Two-gauge section below search |
| `PowerSemicircleGauge` | Top | 180-degree chamber composition gauge |
| `GaugeArcSegment` | Top | Individual party or group arc segment |
| `MajorityMarker` | Top | Halfway line and threshold label |
| `SeatLegend` | Top | Seat colors, labels, and counts |
| `MajorityStatusPanel` | Top | 与党 seats, non-ruling seats, majority status |
| `GaugeTooltip` | Top | Hover/focus detail for a segment |

### Stats And Detail Components

| Component | Used On | Responsibility |
| --- | --- | --- |
| `StatsCounterGrid` | Top | Four compact database counters |
| `StatsCounter` | Top | Single value and label tile |
| `LegislatorProfileHeader` | Detail | Name, kana, house, active status |
| `InfoPanel` | Detail | Basic factual profile fields |
| `DataSourcePanel` | Detail | Official source and retrieval metadata |
| `FutureModulePanel` | Detail | Placeholder area for careers, SNS, voting, policy |

### Interaction Components

| Component | Used On | Responsibility |
| --- | --- | --- |
| `IconButton` | All pages | Menu, back, clear, pagination icons |
| `PrimaryButton` | Search actions | Main submit/action button |
| `TextButton` | Secondary actions | Back, clear, and source links |
| `StatusChip` | All pages | House/status labels |
| `Tooltip` | Gauge, icons | Accessible hover/focus labels |

### Component Build Priority

1. Build `AppShell`, `SiteHeader`, `HudPanel`, `CommandSearch`.
2. Build `PowerMapStrip` and `PowerSemicircleGauge` using placeholder data.
3. Build `RosterPreview`, `RosterTable`, `RosterCard`.
4. Build `/search` filtering with `FilterPanel` and `PaginationControls`.
5. Build `/legislators/[id]` with profile and source panels.

## Initial Frontend Build Scope

First implementation pass:

- Static responsive layout for 3 routes.
- Wire API calls to `/v1/legislators`, `/v1/parties`, `/v1/districts`.
- Use placeholder computed data for top page semicircle gauges until stats API is added.
- Keep all pages visually consistent with the Civic Strategy HUD direction.
