from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from lxml import html
except ModuleNotFoundError:
    html = None


OUT_DIR = Path("data")
SANGIIN_MEMBERS_PATH = OUT_DIR / "sangiin_members.json"
SHUGIIN_MEMBERS_PATH = OUT_DIR / "shugiin_members.json"
ENRICHED_PATH = OUT_DIR / "legislator_profile_enrichment.json"
MISSING_PATH = OUT_DIR / "legislator_profile_missing.json"
SQL_PATH = OUT_DIR / "enrich_legislator_profiles.sql"

SHUGIIN_PROFILE_URL = "https://www.shugiin.go.jp/Internet/itdb_giinprof.nsf/html/profile/{profile_id:03d}.html"
SHUGIIN_LIST_URL = "https://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/syu/{page_index}giin.htm"

ERA_BASE_YEAR = {
    "明治": 1867,
    "大正": 1911,
    "昭和": 1925,
    "平成": 1988,
    "令和": 2018,
}

KANJI_DIGITS = {
    "〇": 0,
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


@dataclass(frozen=True)
class Enrichment:
    name_kanji: str
    name_kana: str
    house: str
    birth_date: str | None
    birth_date_precision: str | None
    birth_date_source_url: str | None
    election_count: int | None
    election_count_note: str | None
    election_count_source_url: str | None
    career_summary: str | None
    career_source_url: str | None
    profile_source_url: str | None
    profile_source_type: str | None
    profile_source_checked_at: str


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; kokkai-giin-db/0.1)"})
    with urlopen(req, timeout=20) as response:
        return response.read()


def clean_text(value: str) -> str:
    value = value.replace("\u3000", " ")
    return re.sub(r"\s+", " ", value).strip()


def normalize_name(value: str) -> str:
    value = clean_text(value)
    value = re.sub(r"\s*\[.*?\]\s*", "", value)
    return value.removesuffix("君").replace(" ", "")


def normalize_digits(value: str) -> str:
    return value.translate(str.maketrans("０１２３４５６７８９", "0123456789"))


def kanji_number(value: str) -> int | None:
    value = normalize_digits(value.strip())
    if not value:
        return None
    if value == "元":
        return 1
    if value.isdigit():
        return int(value)
    total = 0
    current = 0
    for ch in value:
        if ch in KANJI_DIGITS:
            current = KANJI_DIGITS[ch]
        elif ch == "十":
            total += (current or 1) * 10
            current = 0
        elif ch == "百":
            total += (current or 1) * 100
            current = 0
        else:
            return None
    return total + current


def to_date(year: int, month: int | None, day: int | None) -> tuple[str, str] | None:
    precision = "day" if day else "month" if month else "year"
    try:
        parsed = date(year, month or 1, day or 1)
    except ValueError:
        return None
    today = date.today()
    if parsed > today:
        return None
    # Current Diet members must be adults well beyond a normal minimum
    # candidacy age. This keeps update dates and career years out of
    # birth_date even when a page contains misleading date-like text.
    age = today.year - parsed.year - ((today.month, today.day) < (parsed.month, parsed.day))
    if age < 25:
        return None
    return parsed.isoformat(), precision


def parse_birth_date(text: str, *, allow_unlabeled: bool = False) -> tuple[str, str] | None:
    text = normalize_digits(text)
    era_pattern = "|".join(ERA_BASE_YEAR.keys())
    candidates: list[tuple[re.Match[str], tuple[str, str] | None]] = []

    for m in re.finditer(
        rf"({era_pattern})([元〇零一二三四五六七八九十百0-9]+)年"
        r"([〇零一二三四五六七八九十百0-9]+)月"
        r"([〇零一二三四五六七八九十百0-9]+)日",
        text,
    ):
        year = ERA_BASE_YEAR[m.group(1)] + (kanji_number(m.group(2)) or 0)
        candidates.append((m, to_date(year, kanji_number(m.group(3)), kanji_number(m.group(4)))))

    for m in re.finditer(
        rf"({era_pattern})([元〇零一二三四五六七八九十百0-9]+)年"
        r"([〇零一二三四五六七八九十百0-9]+)月",
        text,
    ):
        year = ERA_BASE_YEAR[m.group(1)] + (kanji_number(m.group(2)) or 0)
        candidates.append((m, to_date(year, kanji_number(m.group(3)), None)))

    for m in re.finditer(r"((?:18|19|20)[0-9]{2})年([0-9]{1,2})月([0-9]{1,2})日", text):
        candidates.append((m, to_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))))

    for m in re.finditer(r"((?:18|19|20)[0-9]{2})年([0-9]{1,2})月", text):
        candidates.append((m, to_date(int(m.group(1)), int(m.group(2)), None)))

    for m in re.finditer(r"((?:18|19|20)[0-9]{2})年", text):
        candidates.append((m, to_date(int(m.group(1)), None, None)))

    for m in re.finditer(r"((?:18|19|20)[0-9]{2})[/-]([0-9]{1,2})[/-]([0-9]{1,2})", text):
        candidates.append((m, to_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))))

    valid = [(match, parsed) for match, parsed in candidates if parsed]
    if allow_unlabeled and valid:
        return valid[0][1]

    birth_markers = [m.start() for m in re.finditer(r"生まれ|出生|生[。、．,，]", text)]
    for marker in birth_markers:
        window_start = max(0, marker - 90)
        nearby = [
            (match, parsed)
            for match, parsed in valid
            if window_start <= match.start() and match.end() <= marker
        ]
        if nearby:
            return max(nearby, key=lambda item: item[0].end())[1]

    for match, parsed in valid:
        context = text[match.end() : match.end() + 60]
        if re.search(r"^\s*(?:生まれ|出生|生[。、．,，])", context):
            return parsed
        if "生まれ" in context or "出生" in context:
            return parsed
    return None


def parse_election_count(text: str) -> tuple[int | None, str | None]:
    text = normalize_digits(text)
    patterns = [
        r"当選\s*([0-9一二三四五六七八九十百]+)\s*回(?:（[^）]+）)?",
        r"当選([0-9一二三四五六七八九十百]+)回(?:（[^）]+）)?",
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if not m:
            continue
        note = m.group(0)
        return kanji_number(m.group(1)), note
    return None, None


def text_lines(doc: html.HtmlElement) -> list[str]:
    lines = [clean_text(line) for line in doc.text_content().splitlines()]
    return [line for line in lines if line]


def parse_shugiin_profile(url: str, body: bytes) -> tuple[str | None, str | None, Enrichment | None]:
    doc = html.fromstring(body)
    heading = doc.xpath("string(//h2)")
    heading = clean_text(heading)
    m = re.match(r"(.+?)（(.+?)）", heading)
    if not m:
        return None, None, None

    name = clean_text(m.group(1)).removesuffix("君").strip()
    kana = clean_text(m.group(2))
    lines = text_lines(doc)
    start = next((i for i, line in enumerate(lines) if line == heading), -1)
    relevant = lines[start + 1 :] if start >= 0 else lines
    stop = next((i for i, line in enumerate(relevant) if re.match(r"（令和.*現在）", line)), len(relevant))
    relevant = relevant[:stop]
    profile_text = clean_text(" ".join(relevant))
    birth = parse_birth_date(profile_text)
    election_count, election_note = parse_election_count(profile_text)
    career_summary = profile_text or None

    return (
        normalize_name(name),
        kana,
        Enrichment(
            name_kanji=name,
            name_kana=kana,
            house="shugiin",
            birth_date=birth[0] if birth else None,
            birth_date_precision=birth[1] if birth else None,
            birth_date_source_url=url if birth else None,
            election_count=election_count,
            election_count_note=election_note,
            election_count_source_url=url if election_count is not None else None,
            career_summary=career_summary,
            career_source_url=url if career_summary else None,
            profile_source_url=url,
            profile_source_type="diet_official",
            profile_source_checked_at=date.today().isoformat(),
        ),
    )


def parse_sangiin_profile(member: dict[str, str], body: bytes) -> Enrichment:
    url = member["profile_url"]
    doc = html.fromstring(body)
    lines = text_lines(doc)
    full_text = clean_text(" ".join(lines))
    birth = parse_birth_date(full_text)
    election_count, election_note = parse_election_count(full_text)

    summary_lines: list[str] = []
    end_index = next((i for i, line in enumerate(lines) if re.match(r"（令和.*現在）", line)), len(lines))
    for line in lines[:end_index]:
        if parse_birth_date(line) or (summary_lines and not line.startswith(("所属会派", "選挙区", "参議院"))):
            summary_lines.append(line)
    career_summary = clean_text(" ".join(summary_lines[-4:])) if summary_lines else None

    return Enrichment(
        name_kanji=member["name_kanji"],
        name_kana=member["name_kana"],
        house="sangiin",
        birth_date=birth[0] if birth else None,
        birth_date_precision=birth[1] if birth else None,
        birth_date_source_url=url if birth else None,
        election_count=election_count,
        election_count_note=election_note,
        election_count_source_url=url if election_count is not None else None,
        career_summary=career_summary,
        career_source_url=url if career_summary else None,
        profile_source_url=url,
        profile_source_type="diet_official",
        profile_source_checked_at=date.today().isoformat(),
    )


def build_shugiin_profile_index() -> dict[str, Enrichment]:
    profiles: dict[str, Enrichment] = {}
    for profile_id in range(1, 560):
        url = SHUGIIN_PROFILE_URL.format(profile_id=profile_id)
        try:
            body = fetch(url)
        except HTTPError as exc:
            if exc.code == 404:
                continue
            print(f"warn: failed {url}: {exc}")
            continue
        except (URLError, TimeoutError) as exc:
            print(f"warn: failed {url}: {exc}")
            continue

        key, _kana, enrichment = parse_shugiin_profile(url, body)
        if key and enrichment:
            profiles[key] = enrichment
        time.sleep(0.03)
    return profiles


def build_sangiin_enrichments() -> list[Enrichment]:
    members = json.loads(SANGIIN_MEMBERS_PATH.read_text(encoding="utf-8"))
    enrichments: list[Enrichment] = []
    for member in members:
        url = member.get("profile_url")
        if not url:
            continue
        try:
            enrichments.append(parse_sangiin_profile(member, fetch(url)))
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"warn: failed {url}: {exc}")
        time.sleep(0.03)
    return enrichments


def build_shugiin_list_enrichments() -> dict[str, Enrichment]:
    profiles: dict[str, Enrichment] = {}
    for page_index in range(1, 11):
        url = SHUGIIN_LIST_URL.format(page_index=page_index)
        try:
            body = fetch(url)
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"warn: failed {url}: {exc}")
            continue
        doc = html.fromstring(body.decode("shift_jis", "replace"))
        for row in doc.xpath("//tr"):
            cells = row.xpath("./td")
            values = [clean_text(cell.text_content()) for cell in cells]
            if len(values) != 5 or values[0] == "氏名":
                continue
            name = clean_text(values[0]).removesuffix("君").strip()
            kana = clean_text(values[1])
            raw_count = normalize_digits(values[4])
            count_match = re.match(r"([0-9一二三四五六七八九十百]+)", raw_count)
            count = kanji_number(count_match.group(1)) if count_match else None
            note = f"当選{values[4]}回" if values[4] else None
            profiles[normalize_name(name)] = Enrichment(
                name_kanji=name,
                name_kana=kana,
                house="shugiin",
                birth_date=None,
                birth_date_precision=None,
                birth_date_source_url=None,
                election_count=count,
                election_count_note=note or values[4],
                election_count_source_url=url if count is not None else None,
                career_summary=None,
                career_source_url=None,
                profile_source_url=url,
                profile_source_type="diet_official",
                profile_source_checked_at=date.today().isoformat(),
            )
    return profiles


def sql_literal(value: str | int | None) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, int):
        return str(value)
    return "'" + value.replace("'", "''") + "'"


def build_sql(enrichments: list[Enrichment]) -> str:
    rows = sorted(enrichments, key=lambda item: (item.house, item.name_kana, item.name_kanji))
    values = ",\n".join(
        "("
        + ", ".join(
            [
                sql_literal(row.name_kanji),
                sql_literal(row.name_kana),
                sql_literal(row.house),
                sql_literal(row.birth_date),
                sql_literal(row.birth_date_precision),
                sql_literal(row.birth_date_source_url),
                sql_literal(row.election_count),
                sql_literal(row.election_count_note),
                sql_literal(row.election_count_source_url),
                sql_literal(row.career_summary),
                sql_literal(row.career_source_url),
                sql_literal(row.profile_source_url),
                sql_literal(row.profile_source_type),
                sql_literal(row.profile_source_checked_at),
            ]
        )
        + ")"
        for row in rows
    )
    return f"""-- Generated at {datetime.now(timezone.utc).isoformat()}
-- Sources: House of Representatives / House of Councillors official profile pages.

update public.legislators as l
set
  birth_date = v.birth_date::date,
  birth_date_precision = v.birth_date_precision,
  birth_date_source_url = v.birth_date_source_url,
  election_count = v.election_count,
  election_count_note = v.election_count_note,
  election_count_source_url = v.election_count_source_url,
  career_summary = v.career_summary,
  career_source_url = v.career_source_url,
  profile_source_url = v.profile_source_url,
  profile_source_type = v.profile_source_type,
  profile_source_checked_at = v.profile_source_checked_at::date,
  scraped_at = now(),
  updated_at = now()
from (
  values
{values}
) as v(
  name_kanji,
  name_kana,
  house,
  birth_date,
  birth_date_precision,
  birth_date_source_url,
  election_count,
  election_count_note,
  election_count_source_url,
  career_summary,
  career_source_url,
  profile_source_url,
  profile_source_type,
  profile_source_checked_at
)
where l.name_kanji = v.name_kanji
  and l.name_kana = v.name_kana
  and l.house = v.house;

insert into public.scrape_logs (source, status, records_updated, error_message)
values ('official_profile_enrichment', 'success', {len(rows)}, 'Enriched legislator profiles from official Diet profile pages');
"""


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    shugiin_members = json.loads(SHUGIIN_MEMBERS_PATH.read_text(encoding="utf-8"))
    shugiin_profiles = build_shugiin_profile_index()
    shugiin_list_profiles = build_shugiin_list_enrichments()
    enrichments = build_sangiin_enrichments()
    missing: list[dict[str, str]] = []

    for member in shugiin_members:
        key = normalize_name(member["name_kanji"])
        profile = shugiin_profiles.get(key)
        if not profile:
            profile = shugiin_list_profiles.get(key)
        if profile:
            enrichments.append(profile)
        else:
            missing.append(
                {
                    "name_kanji": member["name_kanji"],
                    "name_kana": member["name_kana"],
                    "house": "shugiin",
                    "next_source": "party_official_then_personal_official",
                }
            )

    for item in enrichments:
        if not item.birth_date or not item.career_summary:
            missing.append(
                {
                    "name_kanji": item.name_kanji,
                    "name_kana": item.name_kana,
                    "house": item.house,
                    "profile_source_url": item.profile_source_url or "",
                    "missing_birth_date": str(not item.birth_date),
                    "missing_career_summary": str(not item.career_summary),
                    "next_source": "party_official_then_personal_official",
                }
            )

    ENRICHED_PATH.write_text(
        json.dumps([asdict(item) for item in enrichments], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    MISSING_PATH.write_text(json.dumps(missing, ensure_ascii=False, indent=2), encoding="utf-8")
    SQL_PATH.write_text(build_sql(enrichments), encoding="utf-8")

    print(f"enriched={len(enrichments)}")
    print(f"with_birth_date={sum(1 for item in enrichments if item.birth_date)}")
    print(f"with_election_count={sum(1 for item in enrichments if item.election_count is not None)}")
    print(f"with_career_summary={sum(1 for item in enrichments if item.career_summary)}")
    print(f"missing_or_incomplete={len(missing)}")
    print(f"json={ENRICHED_PATH}")
    print(f"missing={MISSING_PATH}")
    print(f"sql={SQL_PATH}")


if __name__ == "__main__":
    main()
