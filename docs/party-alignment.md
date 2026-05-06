# Party Alignment

This document records the current party alignment approach used for the power map.

## Current Rule

As of 2026-05-05, `public.parties.alignment` uses:

- `ruling`: 自由民主党, 日本維新の会
- `opposition`: parties/caucuses not in the ruling coalition
- `other`: 無所属

The external source for the ruling coalition classification is:

- https://www.kantei.go.jp/jp/kakugikettei/2026/_00004.html

The source states that the Takaichi Cabinet is based on the coalition agreement between the Liberal Democratic Party and the Japan Innovation Party.

## Rank Rule

`alignment_rank` is not a manually asserted political judgment.

For the power map, it is derived per house:

1. Filter `active_legislators` to either `shugiin` or `sangiin`.
2. Count active members per party inside that house.
3. Partition parties by `alignment`.
4. Sort by active member count descending.
5. Use party name ascending as the tie-breaker.
6. Return the count used in `alignment_rank_member_count`.

`GET /parties?house=shugiin` and `GET /parties?house=sangiin` compute these house-specific ranks at API time. `GET /parties` without a `house` parameter returns the stored aggregate party master fields.

The older aggregate table columns remain for compatibility, but the frontend power map should use the house-specific API response.

## House-Specific Rank Query

```sql
with member_counts as (
  select
    p.id,
    p.name,
    p.alignment,
    count(al.id)::integer as member_count
  from public.parties p
  join public.active_legislators al on al.party_name = p.name
  where al.house = 'shugiin'
  group by p.id, p.name, p.alignment
), ranked as (
  select
    id,
    name,
    alignment,
    member_count,
    row_number() over (
      partition by alignment
      order by member_count desc, name asc
    ) as alignment_rank
  from member_counts
)
select * from ranked;
```

## Aggregate Recompute SQL

This is retained only for the stored aggregate columns on `public.parties`.

```sql
with member_counts as (
  select
    p.id,
    p.name,
    count(al.id)::integer as member_count,
    case
      when p.name in ('自由民主党', '日本維新の会') then 'ruling'
      when p.name = '無所属' then 'other'
      else 'opposition'
    end as next_alignment
  from public.parties p
  left join public.active_legislators al on al.party_name = p.name
  group by p.id, p.name
), ranked as (
  select
    id,
    next_alignment,
    member_count,
    row_number() over (
      partition by next_alignment
      order by member_count desc, name asc
    ) as next_rank
  from member_counts
)
update public.parties p
set
  alignment = ranked.next_alignment,
  alignment_rank = ranked.next_rank,
  alignment_rank_member_count = ranked.member_count,
  alignment_basis = 'alignment: 2026-01-23 Kantei statement identifies LDP-JIP coalition; aggregate rank: active_legislators member count desc within alignment, party name asc tie-breaker',
  alignment_source_url = 'https://www.kantei.go.jp/jp/kakugikettei/2026/_00004.html',
  alignment_source_checked_at = date '2026-05-05',
  updated_at = now()
from ranked
where p.id = ranked.id;
```
