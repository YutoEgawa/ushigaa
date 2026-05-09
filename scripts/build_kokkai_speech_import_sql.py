from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


KOKKAI_API_URL = "https://kokkai.ndl.go.jp/api/speech"
DEFAULT_FROM_DATE = "2023-01-01"
DEFAULT_OUT = Path("data/import_kokkai_speeches.sql")
USER_AGENT = "ushigaa-kokkai-import/0.1"
SQL_CHUNK_SIZE = 500


@dataclass(frozen=True)
class Legislator:
    id: str
    name_kanji: str
    name_kana: str
    house: str


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.replace("\u3000", " ")
    return re.sub(r"\s+", " ", value).strip()


def normalize_name(value: str | None) -> str:
    value = clean_text(value)
    value = re.sub(r"\s*\[.*?\]\s*", "", value)
    return value.removesuffix("君").replace(" ", "")


def get_json(url: str, *, headers: dict[str, str] | None = None, timeout: int = 30) -> Any:
    request = Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_supabase_legislators(limit: int | None, names: list[str] | None) -> list[Legislator]:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY are required.")

    params: dict[str, str] = {
        "select": "id,name_kanji,name_kana,house",
        "status": "eq.active",
        "order": "name_kana.asc",
    }
    if names:
        escaped = ",".join(f'"{name}"' for name in names)
        params["name_kanji"] = f"in.({escaped})"
    if limit:
        params["limit"] = str(limit)

    url = f"{supabase_url.rstrip('/')}/rest/v1/legislators?{urlencode(params)}"
    rows = get_json(
        url,
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Accept": "application/json",
        },
    )
    return [
        Legislator(
            id=row["id"],
            name_kanji=row["name_kanji"],
            name_kana=row.get("name_kana") or "",
            house=row.get("house") or "",
        )
        for row in rows
    ]


def fetch_kokkai_page(speaker: str, from_date: str, start_record: int, maximum_records: int) -> dict[str, Any]:
    params = urlencode(
        {
            "speaker": speaker,
            "from": from_date,
            "startRecord": str(start_record),
            "maximumRecords": str(maximum_records),
            "recordPacking": "json",
        }
    )
    return get_json(f"{KOKKAI_API_URL}?{params}")


def fetch_question_records(
    legislator: Legislator,
    *,
    from_date: str,
    page_size: int,
    max_pages: int | None,
    sleep_seconds: float,
) -> list[dict[str, Any]]:
    search_speaker = normalize_name(legislator.name_kanji)
    records: list[dict[str, Any]] = []
    start_record = 1
    page_count = 0

    while True:
        page_count += 1
        data = fetch_kokkai_page(search_speaker, from_date, start_record, page_size)
        page_records = data.get("speechRecord") or []
        for record in page_records:
            if normalize_name(record.get("speaker")) != search_speaker:
                continue
            if record.get("speakerPosition") is not None:
                continue
            if not clean_text(record.get("speech")):
                continue
            records.append({**record, "_legislator_id": legislator.id})

        next_record = data.get("nextRecordPosition")
        if not next_record or not page_records:
            break
        if max_pages and page_count >= max_pages:
            break
        start_record = int(next_record)
        time.sleep(sleep_seconds)

    return records


def sql_literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    return "'" + text.replace("'", "''") + "'"


def values_list(rows: list[tuple[object, ...]]) -> str:
    return ",\n".join("(" + ", ".join(sql_literal(value) for value in row) + ")" for row in rows)


def chunks(rows: list[tuple[object, ...]], size: int = SQL_CHUNK_SIZE) -> list[list[tuple[object, ...]]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def build_sql(records: list[dict[str, Any]], *, from_date: str) -> str:
    meeting_rows = sorted(
        {
            (
                clean_text(record.get("issueID")),
                clean_text(record.get("nameOfHouse")) or None,
                clean_text(record.get("nameOfMeeting")),
                clean_text(record.get("date")),
            )
            for record in records
            if clean_text(record.get("issueID")) and clean_text(record.get("nameOfMeeting")) and clean_text(record.get("date"))
        }
    )
    speech_rows = sorted(
        {
            (
                record["_legislator_id"],
                clean_text(record.get("speechID")),
                clean_text(record.get("issueID")),
                int(record["speechOrder"]) if str(record.get("speechOrder") or "").isdigit() else None,
                clean_text(record.get("speaker")),
                clean_text(record.get("speakerPosition")) or None,
                clean_text(record.get("speech")),
            )
            for record in records
            if clean_text(record.get("speechID")) and clean_text(record.get("issueID"))
        },
        key=lambda row: (row[2], row[3] or 0, row[1]),
    )

    if not meeting_rows or not speech_rows:
        return f"""-- Generated at {datetime.now(timezone.utc).isoformat()}
-- from_date={from_date}
-- No question-candidate records found.
"""

    parts = [
        f"""-- Generated at {datetime.now(timezone.utc).isoformat()}
-- from_date={from_date}
-- question_candidate_speeches={len(speech_rows)}
"""
    ]
    for chunk in chunks(meeting_rows):
        parts.append(
            f"""
insert into public.kokkai_meetings (
  source_issue_id,
  name_of_house,
  name_of_meeting,
  date
)
values
{values_list(chunk)}
on conflict (source_issue_id) do update set
  name_of_house = excluded.name_of_house,
  name_of_meeting = excluded.name_of_meeting,
  date = excluded.date,
  updated_at = now();
"""
        )
    for chunk in chunks(speech_rows):
        parts.append(
            f"""
insert into public.kokkai_speeches (
  legislator_id,
  meeting_id,
  source_speech_id,
  source_issue_id,
  speech_order,
  speaker,
  speaker_position,
  speech
)
select
  v.legislator_id::uuid,
  m.id,
  v.source_speech_id,
  v.source_issue_id,
  v.speech_order,
  v.speaker,
  v.speaker_position,
  v.speech
from (
  values
{values_list(chunk)}
) as v(
  legislator_id,
  source_speech_id,
  source_issue_id,
  speech_order,
  speaker,
  speaker_position,
  speech
)
join public.kokkai_meetings m on m.source_issue_id = v.source_issue_id
on conflict (source_speech_id) do update set
  legislator_id = excluded.legislator_id,
  meeting_id = excluded.meeting_id,
  source_issue_id = excluded.source_issue_id,
  speech_order = excluded.speech_order,
  speaker = excluded.speaker,
  speaker_position = excluded.speaker_position,
  speech = excluded.speech,
  updated_at = now();
"""
        )
    parts.append(group_sync_sql())
    return "\n".join(parts)


def group_sync_sql() -> str:
    return """
insert into public.kokkai_question_groups (
  legislator_id,
  meeting_id,
  speaker,
  speech_count,
  speech,
  source_issue_ids,
  source_speech_ids,
  first_speech_order,
  last_speech_order
)
select
  s.legislator_id,
  s.meeting_id,
  s.speaker,
  count(*)::integer as speech_count,
  string_agg(s.speech, E'\\n\\n' order by s.speech_order nulls last, s.source_speech_id) as speech,
  array_agg(distinct s.source_issue_id) as source_issue_ids,
  array_agg(s.source_speech_id order by s.speech_order nulls last, s.source_speech_id) as source_speech_ids,
  min(s.speech_order) as first_speech_order,
  max(s.speech_order) as last_speech_order
from public.kokkai_speeches s
where s.speaker_position is null
group by s.legislator_id, s.meeting_id, s.speaker
on conflict (legislator_id, meeting_id, speaker) do update set
  speech_count = excluded.speech_count,
  speech = excluded.speech,
  source_issue_ids = excluded.source_issue_ids,
  source_speech_ids = excluded.source_speech_ids,
  first_speech_order = excluded.first_speech_order,
  last_speech_order = excluded.last_speech_order,
  updated_at = now();
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Kokkai speech import SQL for Ushigaa.")
    parser.add_argument("--from-date", default=DEFAULT_FROM_DATE)
    parser.add_argument("--limit", type=int, default=5, help="Limit legislators fetched from Supabase.")
    parser.add_argument("--names", nargs="*", help="Specific Supabase name_kanji values to import.")
    parser.add_argument("--page-size", type=int, default=100, help="Kokkai API maximumRecords per request.")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional page cap per legislator.")
    parser.add_argument("--sleep", type=float, default=0.4, help="Delay between Kokkai API requests.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv()
    legislators = fetch_supabase_legislators(None if args.names else args.limit, args.names)
    if not legislators:
        print("No legislators found.", file=sys.stderr)
        return 1

    all_records: list[dict[str, Any]] = []
    for index, legislator in enumerate(legislators):
        records = fetch_question_records(
            legislator,
            from_date=args.from_date,
            page_size=args.page_size,
            max_pages=args.max_pages,
            sleep_seconds=args.sleep,
        )
        all_records.extend(records)
        print(f"{legislator.name_kanji}: question_candidate_speeches={len(records)}")
        if index < len(legislators) - 1:
            time.sleep(args.sleep)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_sql(all_records, from_date=args.from_date), encoding="utf-8")
    print(f"sql={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
