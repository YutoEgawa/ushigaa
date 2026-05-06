from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from lxml import html


BASE_URL = "https://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/syu"
OUT_DIR = Path("data")

PARTY_SHORT_NAMES = {
    "自民": "自由民主党",
    "中道": "中道改革連合・無所属",
    "維新": "日本維新の会",
    "国民": "国民民主党",
    "参政": "参政党",
    "みらい": "チームみらい",
    "共産": "日本共産党",
    "無": "無所属",
}


@dataclass(frozen=True)
class ShugiinMember:
    name_kanji: str
    name_kana: str
    party_short: str
    party_name: str
    district_name: str
    district_type: str
    block_name: str | None


def fetch_page(index: int) -> str:
    request = Request(
        f"{BASE_URL}/{index}giin.htm",
        headers={"User-Agent": "Mozilla/5.0 (compatible; kokkai-giin-db/0.1)"},
    )
    body = urlopen(request, timeout=20).read()
    return body.decode("shift_jis", "replace")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u3000", " ")).strip()


def clean_name(text: str) -> str:
    return clean_text(text).removesuffix("君").strip()


def normalize_district(raw: str) -> tuple[str, str, str | None]:
    raw = clean_text(raw)
    if raw.startswith("（比）"):
        name = raw.replace("（比）", "", 1)
        return name, "proportional", name
    return raw, "single", None


def parse_members() -> list[ShugiinMember]:
    members: list[ShugiinMember] = []
    for page_index in range(1, 11):
        doc = html.fromstring(fetch_page(page_index))
        for row in doc.xpath("//tr"):
            cells = row.xpath("./td")
            values = [clean_text(cell.text_content()) for cell in cells]
            if len(values) != 5 or values[0] == "氏名":
                continue

            party_short = values[2]
            district_name, district_type, block_name = normalize_district(values[3])
            members.append(
                ShugiinMember(
                    name_kanji=clean_name(values[0]),
                    name_kana=clean_text(values[1]),
                    party_short=party_short,
                    party_name=PARTY_SHORT_NAMES.get(party_short, party_short),
                    district_name=district_name,
                    district_type=district_type,
                    block_name=block_name,
                )
            )
    return members


def sql_literal(value: str | None) -> str:
    if value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


def values_list(rows: list[tuple[str | None, ...]]) -> str:
    return ",\n".join("(" + ", ".join(sql_literal(value) for value in row) + ")" for row in rows)


def build_sql(members: list[ShugiinMember]) -> str:
    parties = sorted({(m.party_name, m.party_short) for m in members})
    districts = sorted({(m.district_name, m.district_type, m.block_name) for m in members})
    legislators = sorted({(m.name_kanji, m.name_kana) for m in members})
    terms = sorted({(m.name_kanji, m.name_kana, m.party_name, m.district_name) for m in members})

    return f"""-- Generated from {BASE_URL}/{{1-10}}giin.htm
-- Generated at {datetime.now(timezone.utc).isoformat()}

insert into public.parties (name, name_short)
values
{values_list(parties)}
on conflict (name) do nothing;

insert into public.districts (house, type, name, block_name)
values
{values_list([("shugiin", district_type, name, block_name) for name, district_type, block_name in districts])}
on conflict (house, name) do update set
  type = excluded.type,
  block_name = excluded.block_name;

insert into public.legislators (name_kanji, name_kana, house, status, photo_url, scraped_at)
values
{values_list([(name, kana, "shugiin", "active", None, None) for name, kana in legislators])}
on conflict (name_kanji, name_kana, house) do update set
  status = excluded.status,
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
  2024,
  'general',
  date '2024-10-27',
  date '2028-10-26'
from (
  values
{values_list(terms)}
) as v(name_kanji, name_kana, party_name, district_name)
join public.legislators l
  on l.name_kanji = v.name_kanji
 and l.name_kana = v.name_kana
 and l.house = 'shugiin'
left join public.parties p on p.name = v.party_name
left join public.districts d
  on d.house = 'shugiin'
 and d.name = v.district_name
on conflict (legislator_id, election_type, election_year) do update set
  district_id = excluded.district_id,
  party_id = excluded.party_id,
  term_start = excluded.term_start,
  term_end = excluded.term_end;
"""


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    members = parse_members()
    if len(members) < 450:
        raise RuntimeError(f"Expected at least 450 members, got {len(members)}")

    (OUT_DIR / "shugiin_members.json").write_text(
        json.dumps([asdict(member) for member in members], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT_DIR / "import_shugiin.sql").write_text(build_sql(members), encoding="utf-8")
    print(f"members={len(members)}")
    print(f"sql={OUT_DIR / 'import_shugiin.sql'}")


if __name__ == "__main__":
    main()
