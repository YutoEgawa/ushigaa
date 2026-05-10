from __future__ import annotations

import argparse
import csv
import json
import os
import re
from dataclasses import dataclass
from datetime import date
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


KANTEI_INDEX_URL = "https://www.kantei.go.jp/jp/rekidainaikaku/index.html"
CAO_ARCHIVE_URL = "https://www.cao.go.jp/minister/archive.html"
SOURCE_START_DATE = date(2023, 1, 1)
SOURCE_CHECKED_AT = date(2026, 5, 10)
USER_AGENT = "ushigaa-government-role-import/0.1"
KNOWN_CABINET_END_DATES = {
    "第1次石破内閣": date(2024, 11, 11),
    "第2次石破内閣": date(2025, 10, 21),
    "第1次高市内閣": date(2026, 2, 18),
}


@dataclass(frozen=True)
class Legislator:
    id: str
    name_kanji: str
    normalized_name: str


@dataclass(frozen=True)
class RoleRecord:
    legislator_id: str | None
    name_kanji: str
    normalized_name: str
    role_type: str
    role_title: str
    cabinet_name: str
    cabinet_started_on: date | None
    cabinet_ended_on: date | None
    source_name: str
    source_url: str
    source_checked_at: date


class TextLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._href_stack: list[str | None] = []
        self._current_href: str | None = None
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"p", "li", "h1", "h2", "h3", "h4", "dt", "dd", "tr", "th", "td", "br"}:
            self._flush_text()
        if tag == "img":
            alt = dict(attrs).get("alt")
            if alt:
                self.lines.append(alt)
                if self._current_href is not None:
                    self._current_text.append(alt)
        if tag == "a":
            self._href_stack.append(self._current_href)
            self._current_href = dict(attrs).get("href")
            self._current_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            text = compact_text("".join(self._current_text))
            if text and self._current_href:
                self.links.append((text, self._current_href))
            self._current_href = self._href_stack.pop() if self._href_stack else None
            self._current_text = []
        if tag in {"p", "li", "h1", "h2", "h3", "h4", "dt", "dd", "tr", "th", "td"}:
            self._flush_text()

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_text.append(data)
        self.lines.append(data)

    def _flush_text(self) -> None:
        self.lines.append("\n")

    def text_lines(self) -> list[str]:
        text = unescape("".join(self.lines))
        return [compact_text(line) for line in text.splitlines() if compact_text(line)]


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_name(value: str) -> str:
    return re.sub(r"[\s\u3000󠄀]", "", value)


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as response:
        return response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")


def parse_html(url: str) -> TextLinkParser:
    parser = TextLinkParser()
    parser.feed(fetch_html(url))
    for index, (text, href) in enumerate(parser.links):
        parser.links[index] = (text, urljoin(url, href))
    return parser


def parse_japanese_era_date(value: str) -> date | None:
    match = re.search(r"(令和|平成)(元|\d+)年(\d+)月(\d+)日", value)
    if not match:
        return None
    era, year_text, month_text, day_text = match.groups()
    year = 1 if year_text == "元" else int(year_text)
    western_year = year + (2018 if era == "令和" else 1988)
    return date(western_year, int(month_text), int(day_text))


def fetch_supabase_legislators() -> dict[str, Legislator]:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if "=" not in line or line.strip().startswith("#"):
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY are required")

    params = {
        "select": "id,name_kanji",
        "limit": 1000,
    }
    url = f"{supabase_url.rstrip('/')}/rest/v1/active_legislators?{urlencode(params)}"
    req = Request(
        url,
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Accept": "application/json",
        },
    )
    with urlopen(req, timeout=30) as response:
        rows = json.loads(response.read().decode("utf-8"))
    return {
        normalize_name(row["name_kanji"]): Legislator(
            id=row["id"],
            name_kanji=row["name_kanji"],
            normalized_name=normalize_name(row["name_kanji"]),
        )
        for row in rows
    }


def kantei_prime_minister_pages() -> list[str]:
    parser = parse_html(KANTEI_INDEX_URL)
    pages: list[tuple[int, str]] = []
    for _text, href in parser.links:
        match = re.search(r"/rekidainaikaku/(\d+)\.html$", href)
        if match and int(match.group(1)) >= 101:
            pages.append((int(match.group(1)), href))
    return [href for _number, href in sorted(set(pages))]


def parse_kantei_roles(url: str, legislators: dict[str, Legislator]) -> list[RoleRecord]:
    parser = parse_html(url)
    lines = parser.text_lines()
    source_records: list[RoleRecord] = []
    cabinet_sections: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    role_type: str | None = None
    role_lines: list[str] = []
    latest_start: date | None = None

    for line in lines:
        if line.startswith("第") and "内閣" in line and "名簿" not in line and "開く" not in line:
            if current:
                cabinet_sections.append(current)
            current = {"cabinet_name": line, "started_on": None, "records": []}
            role_type = None
            role_lines = []
            continue

        start_date = parse_japanese_era_date(line)
        if current and start_date and "発足" in line:
            current["started_on"] = start_date
            latest_start = start_date
            continue

        if not current:
            continue

        if "閣僚名簿" in line:
            role_type = "minister"
            role_lines = []
            continue
        if "副大臣名簿" in line:
            role_type = "senior_vice_minister"
            role_lines = []
            continue
        if "大臣政務官名簿" in line:
            role_type = "parliamentary_vice_minister"
            role_lines = []
            continue
        if "名簿" in line:
            role_type = None
            role_lines = []
            continue
        if line in {"職名 氏名", "職名", "氏名"} or "開く 閉じる" in line:
            continue

        person = parse_person_line(line)
        if role_type and person:
            name = person
            role_title = "、".join(clean_role_line(item) for item in role_lines if clean_role_line(item))
            if role_title and is_target_role(role_type, role_title):
                source_records.append(
                    build_record(
                        legislators=legislators,
                        name_kanji=name,
                        role_type=role_type,
                        role_title=role_title,
                        cabinet_name=str(current["cabinet_name"]),
                        cabinet_started_on=current.get("started_on") if isinstance(current.get("started_on"), date) else latest_start,
                        source_name="kantei_rekidai_naikaku",
                        source_url=url,
                    )
                )
            role_lines = []
            continue

        if role_type and not is_noise_line(line):
            role_lines.append(line)

    if current:
        cabinet_sections.append(current)

    starts = [
        section.get("started_on") if isinstance(section.get("started_on"), date) else None
        for section in cabinet_sections
    ]
    section_end_by_name: dict[str, date | None] = {}
    for index, section in enumerate(cabinet_sections):
        following = next((item for item in starts[index + 1 :] if item), None)
        cabinet_name = str(section["cabinet_name"])
        section_end_by_name[cabinet_name] = KNOWN_CABINET_END_DATES.get(cabinet_name, following)

    records: list[RoleRecord] = []
    for record in source_records:
        ended_on = section_end_by_name.get(record.cabinet_name)
        if overlaps_source_window(record.cabinet_started_on, ended_on):
            records.append(
                RoleRecord(
                    **{
                        **record.__dict__,
                        "cabinet_ended_on": ended_on,
                    }
                )
            )
    return records


def parse_cao_roles(url: str, legislators: dict[str, Legislator]) -> list[RoleRecord]:
    parser = parse_html(url)
    lines = parser.text_lines()
    cabinet_name = next((line for line in lines if "内閣" in line), "内閣府")
    records: list[RoleRecord] = []
    role_type: str | None = None
    for line in lines:
        if line == "大臣":
            role_type = "minister"
            continue
        if line == "副大臣":
            role_type = "senior_vice_minister"
            continue
        if line == "大臣政務官":
            role_type = "parliamentary_vice_minister"
            continue
        if not role_type:
            continue
        person = parse_person_line(line) or parse_cao_person_with_role(line)
        if not person:
            continue
        role_title = line.replace(person, "").strip(" 、")
        records.append(
            build_record(
                legislators=legislators,
                name_kanji=person,
                role_type=role_type,
                role_title=role_title or role_label(role_type),
                cabinet_name=cabinet_name,
                cabinet_started_on=None,
                source_name="cao_minister_archive",
                source_url=url,
            )
        )
    return records


def parse_person_line(line: str) -> str | None:
    match = re.match(r"^([一-龥ぁ-んァ-ヶー・\s󠄀]+?)（[ぁ-んァ-ヶー・\s]+）$", line)
    if not match:
        return None
    name = compact_text(match.group(1))
    if not re.search(r"[一-龥]", name):
        return None
    return name


def parse_cao_person_with_role(line: str) -> str | None:
    match = re.match(r"^([一-龥ぁ-んァ-ヶー・\s󠄀]+?)\s+内閣府", line)
    if not match:
        return None
    name = compact_text(match.group(1))
    if not re.search(r"[一-龥]", name):
        return None
    return name


def clean_role_line(line: str) -> str:
    line = re.sub(r"令和[元\d]+年\d+月\d+日.*", "", line)
    line = re.sub(r"平成[元\d]+年\d+月\d+日.*", "", line)
    return compact_text(line.strip("、"))


def is_target_role(role_type: str, role_title: str) -> bool:
    if role_type != "minister":
        return True
    if "副大臣" in role_title or "大臣政務官" in role_title:
        return False
    excluded_titles = ["内閣官房副長官", "内閣法制局長官", "内閣総理大臣補佐官"]
    if any(title in role_title for title in excluded_titles):
        return False
    minister_titles = ["大臣", "内閣官房長官", "国家公安委員会委員長"]
    return any(title in role_title for title in minister_titles)


def is_noise_line(line: str) -> bool:
    return (
        line.startswith("このページの先頭")
        or line == "詳細"
        or line.startswith("Image")
        or line.startswith("プロフィール")
        or line.startswith("生年月日")
        or line.startswith("出身地")
        or line.startswith("就任時年齢")
        or line.startswith("在職")
    )


def role_label(role_type: str) -> str:
    return {
        "prime_minister": "総理大臣",
        "minister": "大臣",
        "senior_vice_minister": "副大臣",
        "parliamentary_vice_minister": "大臣政務官",
    }[role_type]


def classify_role_type(role_type: str, role_title: str) -> str:
    if role_type == "minister" and "内閣総理大臣" in role_title:
        return "prime_minister"
    return role_type


def build_record(
    *,
    legislators: dict[str, Legislator],
    name_kanji: str,
    role_type: str,
    role_title: str,
    cabinet_name: str,
    cabinet_started_on: date | None,
    source_name: str,
    source_url: str,
) -> RoleRecord:
    normalized_name = normalize_name(name_kanji)
    legislator = legislators.get(normalized_name)
    classified_role_type = classify_role_type(role_type, role_title)
    return RoleRecord(
        legislator_id=legislator.id if legislator else None,
        name_kanji=legislator.name_kanji if legislator else name_kanji,
        normalized_name=normalized_name,
        role_type=classified_role_type,
        role_title=role_title,
        cabinet_name=cabinet_name,
        cabinet_started_on=cabinet_started_on,
        cabinet_ended_on=None,
        source_name=source_name,
        source_url=source_url,
        source_checked_at=SOURCE_CHECKED_AT,
    )


def overlaps_source_window(started_on: date | None, ended_on: date | None) -> bool:
    if started_on is None:
        return True
    if ended_on is None:
        return started_on >= SOURCE_START_DATE
    return ended_on >= SOURCE_START_DATE


def dedupe(records: list[RoleRecord]) -> list[RoleRecord]:
    seen: set[tuple[object, ...]] = set()
    unique: list[RoleRecord] = []
    for record in records:
        key = (
            record.normalized_name,
            record.role_type,
            record.role_title,
            record.cabinet_name,
            record.cabinet_started_on,
            record.source_url,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def sql_literal(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, date):
        return "'" + value.isoformat() + "'"
    if isinstance(value, bool):
        return "true" if value else "false"
    return "'" + str(value).replace("'", "''") + "'"


def build_import_sql(records: list[RoleRecord]) -> str:
    columns = [
        "legislator_id",
        "name_kanji",
        "normalized_name",
        "role_type",
        "role_title",
        "cabinet_name",
        "cabinet_started_on",
        "cabinet_ended_on",
        "source_name",
        "source_url",
        "source_checked_at",
    ]
    values = []
    for record in records:
        values.append(
            "("
            + ", ".join(sql_literal(getattr(record, column)) for column in columns)
            + ")"
        )
    return f"""-- Generated from official Cabinet sources on {SOURCE_CHECKED_AT.isoformat()}.
-- Run data/create_government_role_tables.sql before this import.

delete from public.legislator_government_roles
where source_name in ('kantei_rekidai_naikaku', 'cao_minister_archive');

insert into public.legislator_government_roles (
  {", ".join(columns)}
)
values
{",\n".join(values)}
on conflict (normalized_name, role_type, role_title, cabinet_name, cabinet_started_on, source_url)
do update set
  legislator_id = excluded.legislator_id,
  name_kanji = excluded.name_kanji,
  cabinet_ended_on = excluded.cabinet_ended_on,
  source_checked_at = excluded.source_checked_at,
  updated_at = now();
"""


def write_csv(records: list[RoleRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(RoleRecord.__dataclass_fields__.keys()))
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)


def write_flags_csv(records: list[RoleRecord], path: Path) -> None:
    flags: dict[str, dict[str, object]] = {}
    for record in records:
        if not record.legislator_id:
            continue
        item = flags.setdefault(
            record.legislator_id,
            {
                "legislator_id": record.legislator_id,
                "name_kanji": record.name_kanji,
                "has_prime_minister_experience": False,
                "has_minister_experience": False,
                "has_senior_vice_minister_experience": False,
                "has_parliamentary_vice_minister_experience": False,
                "has_executive_government_experience": False,
            },
        )
        if record.role_type == "prime_minister":
            item["has_prime_minister_experience"] = True
        if record.role_type == "minister":
            item["has_minister_experience"] = True
        if record.role_type == "senior_vice_minister":
            item["has_senior_vice_minister_experience"] = True
        if record.role_type == "parliamentary_vice_minister":
            item["has_parliamentary_vice_minister_experience"] = True
        item["has_executive_government_experience"] = True
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(next(iter(flags.values())).keys()))
        writer.writeheader()
        for item in sorted(flags.values(), key=lambda row: str(row["name_kanji"])):
            writer.writerow(item)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-sql", type=Path, default=Path("data/import_government_roles.sql"))
    parser.add_argument("--out-csv", type=Path, default=Path("data/government_roles_official_sources.csv"))
    parser.add_argument("--out-flags-csv", type=Path, default=Path("data/government_role_flags_official_sources.csv"))
    args = parser.parse_args()

    legislators = fetch_supabase_legislators()
    records: list[RoleRecord] = []
    for page_url in kantei_prime_minister_pages():
        records.extend(parse_kantei_roles(page_url, legislators))

    # Cabinet Office archive is retained as an official supplementary source for Cabinet Office posts.
    cao_parser = parse_html(CAO_ARCHIVE_URL)
    for _text, href in cao_parser.links:
        if "/minister/" in href and href.endswith("/index.html"):
            records.extend(parse_cao_roles(href, legislators))

    records = dedupe(records)
    records.sort(key=lambda item: (item.cabinet_started_on or date.min, item.role_type, item.normalized_name, item.role_title))

    write_csv(records, args.out_csv)
    write_flags_csv(records, args.out_flags_csv)
    args.out_sql.write_text(build_import_sql(records), encoding="utf-8")

    matched = sum(1 for record in records if record.legislator_id)
    print(f"records={len(records)}")
    print(f"matched_records={matched}")
    print(f"unmatched_records={len(records) - matched}")
    print(f"sql={args.out_sql}")
    print(f"csv={args.out_csv}")
    print(f"flags_csv={args.out_flags_csv}")


if __name__ == "__main__":
    main()
