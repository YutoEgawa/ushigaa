# Legislator Profile Enrichment

## Source Priority

1. Diet official profile pages
   - House of Councillors profile pages are available from `data/sangiin_members.json`.
   - House of Representatives profile pages were checked by profile ID enumeration, but direct profile URLs returned `404` during the 2026-05-05 run.
2. Party official profile pages
   - Used only for fields missing from Diet official pages.
3. Personal official websites
   - Used only when Diet and party official sources do not provide the field.

## Fields

- `birth_date`
- `birth_date_precision`
- `birth_date_source_url`
- `election_count`
- `election_count_note`
- `election_count_source_url`
- `career_summary`
- `career_source_url`
- `profile_source_url`
- `profile_source_type`
- `profile_source_checked_at`

`birth_date_precision` is required because some profiles provide only year/month, not a full date.

## 2026-05-05 Run

- House of Councillors: 247 / 247 enriched with birth date, election count, and career summary from official profile pages.
- House of Representatives: 465 / 465 enriched with election count from the official alphabetical list.
- House of Representatives: 307 / 465 enriched with birth date from Liberal Democratic Party official member profiles.
- House of Representatives: 296 / 465 enriched with career summary from Liberal Democratic Party official member profiles.
- House of Representatives: 67 additional birth dates and 82 additional career summaries enriched from Japan Innovation Party, Democratic Party For the People, Sanseito, and Japanese Communist Party official sources.
- House of Representatives: 59 birth dates and 59 career summaries refreshed from Centrist Reform Alliance and Team Mirai official sources.
  - Team Mirai profiles use year-level birth dates when only `YYYY年生まれ` is available.
  - Centrist Reform Alliance career summaries combine `役職`, `国会の所属委員会／役職`, `経歴等`, and `学歴`.
- Current House of Representatives coverage: 433 / 465 birth dates, 465 / 465 election counts, 437 / 465 career summaries.
- Remaining House of Representatives profile gaps are mainly Liberal Democratic Party matching misses, independents, and party pages without date/career fields.

## Party Name Normalization

- `国民民主党・無所属クラブ` and `国民民主党・新緑風会` are treated as the same party: `国民民主党`.
- Current database terms have been reassigned to the canonical `国民民主党` party row.
- Import scripts now map the House of Representatives short name `国民` and the House of Councillors short name `民主` to `国民民主党`.
- `チームみらい・無所属`, if encountered in source data, is normalized to `チームみらい`.

## Party Fallback Methods

- Liberal Democratic Party: `https://www.jimin.jp/member/data/member.json` -> official member detail page.
- Japan Innovation Party: `https://o-ishin.jp/member/shugiin/` -> `/member/detail/*.html`.
- Democratic Party For the People: `https://new-kokumin.jp/member` -> `/member/{slug}`.
- Sanseito: official JSON files embedded in `https://sanseito.jp/member/`.
  - `https://sanseito.jp/nppoj/wp-content/themes/wp_310/member_for_newpage.json?20260503`
  - `https://sanseito.jp/2020/wp-content/themes/twentynineteen/member.json?20260413`
- Japanese Communist Party: `https://www.jcp.or.jp/diet_member/house/hor/`.
- Centrist Reform Alliance: `https://craj.jp/members/` -> `/member/{id}`.
- Team Mirai: `https://team-mir.ai/election/shugiin-2026` -> `/election/shugiin-2026/members/{slug}`.
  - Team Mirai currently exposes candidate-period profile pages. When the profile contains only year-level birth data, it is stored as `YYYY-01-01` with `birth_date_precision = 'year'`.

The script uses direct party official indexes/JSON for these parties. Search-engine fallback is disabled for repeatable imports unless explicitly requested.

Generated files:

- `data/legislator_profile_enrichment.json`
- `data/legislator_profile_missing.json`
- `data/enrich_legislator_profiles.sql`
- `data/shugiin_party_profile_enrichment.json`
- `data/shugiin_party_profile_unresolved.json`
- `data/shugiin_profile_remaining.json`
- `data/enrich_shugiin_party_profiles.sql`
