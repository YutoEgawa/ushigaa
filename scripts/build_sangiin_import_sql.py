from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from lxml import html


CURRENT_URL = "https://www.sangiin.go.jp/japanese/joho1/kousei/giin/current/giin.htm"
BASE_URL = "https://www.sangiin.go.jp"
OUT_DIR = Path("data")

PARTY_SHORT_NAMES = {
    "自民": "自由民主党",
    "立憲": "立憲民主党",
    "維新": "日本維新の会",
    "公明": "公明党",
    "民主": "国民民主党",
    "共産": "日本共産党",
    "れ新": "れいわ新選組",
    "参政": "参政党",
    "保守": "日本保守党",
    "みら": "チームみらい",
    "沖縄": "沖縄の風",
    "無所属": "無所属",
    "社民": "社会民主党",
}


@dataclass(frozen=True)
class SangiinMember:
    name_kanji: str
    name_kana: str
    party_short: str
    party_name: str
    district_name: str
    district_type: str
    term_end_jp: str
    profile_url: str | None


def fetch_html(url: str) -> tuple[str, bytes]:
    request = Request(url, headers={"User-Agent": "kokkai-giin-db/0.1 (+data import)"})
    response = urlopen(request, timeout=20)
    final_url = response.geturl()
    return final_url, response.read()


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_name(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"\s*\[.*?\]\s*", "", text)
    return text.strip()


def parse_members(page_url: str, body: bytes) -> list[SangiinMember]:
    doc = html.fromstring(body)
    members: list[SangiinMember] = []

    for row in doc.xpath("//tr"):
        cells = row.xpath("./th|./td")
        values = [clean_text(cell.text_content()) for cell in cells]
        if not values or "議員氏名" in values:
            continue

        link_cell_index = next(
            (idx for idx, cell in enumerate(cells) if cell.xpath(".//a[contains(@href, 'profile')]")),
            None,
        )
        if link_cell_index is None:
            continue

        values = values[link_cell_index:]
        if len(values) < 5:
            continue

        link = cells[link_cell_index].xpath(".//a[contains(@href, 'profile')]/@href")[0]
        name_kanji, name_kana, party_short, district_name, term_end_jp = values[:5]
        party_name = PARTY_SHORT_NAMES.get(party_short, party_short)

        members.append(
            SangiinMember(
                name_kanji=clean_name(name_kanji),
                name_kana=clean_text(name_kana),
                party_short=party_short,
                party_name=party_name,
                district_name=clean_text(district_name),
                district_type="proportional" if district_name == "比例" else "single",
                term_end_jp=clean_text(term_end_jp),
                profile_url=urljoin(page_url, link) if link else None,
            )
        )

    return members


def sql_literal(value: str | None) -> str:
    if value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


def values_list(rows: list[tuple[str | None, ...]]) -> str:
    return ",\n".join("(" + ", ".join(sql_literal(value) for value in row) + ")" for row in rows)


def build_sql(members: list[SangiinMember], source_url: str) -> str:
    parties = sorted({(member.party_name, member.party_short) for member in members})
    districts = sorted({(member.district_name, member.district_type) for member in members})
    legislators = sorted({(member.name_kanji, member.name_kana, member.profile_url) for member in members})
    terms = sorted(
        {
            (
                member.name_kanji,
                member.name_kana,
                member.party_name,
                member.district_name,
                member.term_end_jp,
            )
            for member in members
        }
    )

    return f"""-- Generated from {source_url}
-- Generated at {datetime.now(timezone.utc).isoformat()}

insert into public.parties (name, name_short)
values
{values_list(parties)}
on conflict (name) do update set
  name_short = excluded.name_short,
  updated_at = now();

insert into public.districts (house, type, name, block_name)
values
{values_list([("sangiin", district_type, name, None) for name, district_type in districts])}
on conflict (house, name) do update set
  type = excluded.type,
  block_name = excluded.block_name;

insert into public.legislators (name_kanji, name_kana, house, status, photo_url, scraped_at)
values
{values_list([(name, kana, "sangiin", "active", profile_url, None) for name, kana, profile_url in legislators])}
on conflict (name_kanji, name_kana, house) do update set
  status = excluded.status,
  photo_url = excluded.photo_url,
  scraped_at = now(),
  updated_at = now();

insert into public.legislator_terms (
  legislator_id,
  district_id,
  party_id,
  election_year,
  election_type,
  term_start,
  term_end
)
select
  l.id,
  d.id,
  p.id,
  case when v.term_end_jp like '%10年%' then 2022 else 2025 end as election_year,
  'regular' as election_type,
  case when v.term_end_jp like '%10年%' then date '2022-07-26' else date '2025-07-29' end as term_start,
  case when v.term_end_jp like '%10年%' then date '2028-07-25' else date '2031-07-28' end as term_end
from (
  values
{values_list(terms)}
) as v(name_kanji, name_kana, party_name, district_name, term_end_jp)
join public.legislators l
  on l.name_kanji = v.name_kanji
 and l.name_kana = v.name_kana
 and l.house = 'sangiin'
left join public.parties p on p.name = v.party_name
left join public.districts d
  on d.house = 'sangiin'
 and d.name = v.district_name
on conflict (legislator_id, election_type, election_year) do update set
  district_id = excluded.district_id,
  party_id = excluded.party_id,
  term_start = excluded.term_start,
  term_end = excluded.term_end;

insert into public.scrape_logs (source, status, records_updated, error_message)
values ('sangiin', 'success', {len(members)}, 'Imported from {source_url}');
"""


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    final_url, body = fetch_html(CURRENT_URL)
    members = parse_members(final_url, body)
    if not members:
        doc = html.fromstring(body)
        links = doc.xpath("//a/@href")
        if links:
            final_url = urljoin(final_url, links[0])
            final_url, body = fetch_html(final_url)
            members = parse_members(final_url, body)
    if len(members) < 200:
        raise RuntimeError(f"Expected at least 200 members, got {len(members)}")

    (OUT_DIR / "sangiin_members.json").write_text(
        json.dumps([asdict(member) for member in members], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT_DIR / "import_sangiin.sql").write_text(build_sql(members, final_url), encoding="utf-8")
    print(f"members={len(members)}")
    print(f"sql={OUT_DIR / 'import_sangiin.sql'}")


if __name__ == "__main__":
    main()
