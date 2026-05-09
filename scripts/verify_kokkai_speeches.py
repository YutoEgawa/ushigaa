from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


KOKKAI_API_URL = "https://kokkai.ndl.go.jp/api/speech"
DEFAULT_FROM_DATE = "2023-01-01"
DEFAULT_USER_AGENT = "ushigaa-kokkai-verify/0.1"


@dataclass(frozen=True)
class Legislator:
    id: str | None
    name_kanji: str
    name_kana: str | None = None
    house: str | None = None


@dataclass(frozen=True)
class SpeechGroup:
    date: str
    name_of_meeting: str
    speaker: str
    speech_count: int
    speeches: list[str]


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


def compact_preview(value: str, length: int = 160) -> str:
    value = clean_text(value)
    if len(value) <= length:
        return value
    return f"{value[:length]}..."


def get_json(url: str, *, headers: dict[str, str] | None = None, timeout: int = 20) -> Any:
    request = Request(url, headers={"User-Agent": DEFAULT_USER_AGENT, **(headers or {})})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_supabase_legislators(limit: int) -> list[Legislator]:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY are required when --names is not provided.")

    params = urlencode(
        {
            "select": "id,name_kanji,name_kana,house",
            "status": "eq.active",
            "order": "name_kana.asc",
            "limit": str(limit),
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/legislators?{params}"
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
            id=row.get("id"),
            name_kanji=row["name_kanji"],
            name_kana=row.get("name_kana"),
            house=row.get("house"),
        )
        for row in rows
    ]


def fetch_kokkai_speeches(speaker: str, from_date: str, maximum_records: int) -> dict[str, Any]:
    params = urlencode(
        {
            "speaker": speaker,
            "from": from_date,
            "maximumRecords": str(maximum_records),
            "recordPacking": "json",
        }
    )
    return get_json(f"{KOKKAI_API_URL}?{params}")


def group_question_speeches(records: list[dict[str, Any]], expected_speaker: str) -> list[SpeechGroup]:
    expected_normalized = normalize_name(expected_speaker)
    grouped: dict[tuple[str, str, str], list[str]] = {}

    for record in records:
        speaker = clean_text(record.get("speaker"))
        if normalize_name(speaker) != expected_normalized:
            continue
        if record.get("speakerPosition") is not None:
            continue
        date = clean_text(record.get("date"))
        name_of_meeting = clean_text(record.get("nameOfMeeting"))
        speech = clean_text(record.get("speech"))
        if not date or not name_of_meeting or not speech:
            continue
        grouped.setdefault((date, name_of_meeting, speaker), []).append(speech)

    return [
        SpeechGroup(
            date=date,
            name_of_meeting=name_of_meeting,
            speaker=speaker,
            speech_count=len(speeches),
            speeches=speeches,
        )
        for (date, name_of_meeting, speaker), speeches in sorted(grouped.items(), reverse=True)
    ]


def verify_legislator(legislator: Legislator, *, from_date: str, maximum_records: int) -> dict[str, Any]:
    search_speaker = normalize_name(legislator.name_kanji)
    data = fetch_kokkai_speeches(search_speaker, from_date, maximum_records)
    records = data.get("speechRecord") or []
    exact_records = [
        record
        for record in records
        if normalize_name(record.get("speaker")) == search_speaker
    ]
    question_records = [
        record
        for record in exact_records
        if record.get("speakerPosition") is None
    ]
    groups = group_question_speeches(records, search_speaker)

    return {
        "legislator": legislator,
        "search_speaker": search_speaker,
        "api_total_records": data.get("numberOfRecords"),
        "fetched_records": len(records),
        "exact_speaker_records": len(exact_records),
        "question_candidate_records": len(question_records),
        "question_groups": groups,
    }


def print_result(result: dict[str, Any], *, preview_length: int) -> None:
    legislator: Legislator = result["legislator"]
    groups: list[SpeechGroup] = result["question_groups"]
    print("=" * 80)
    print(
        f"{legislator.name_kanji}"
        f" / search={result['search_speaker']}"
        f" / house={legislator.house or '-'}"
        f" / supabase_id={legislator.id or '-'}"
    )
    print(
        "records:"
        f" api_total={result['api_total_records']}"
        f" fetched={result['fetched_records']}"
        f" exact_speaker={result['exact_speaker_records']}"
        f" speaker_position_null={result['question_candidate_records']}"
        f" grouped_questions={len(groups)}"
    )
    for group in groups[:5]:
        joined_speech = "\n".join(group.speeches)
        print(f"- {group.date} / {group.name_of_meeting} / speeches={group.speech_count}")
        print(f"  {compact_preview(joined_speech, preview_length)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify Kokkai API speaker matching for Ushigaa without saving records."
    )
    parser.add_argument("--from-date", default=DEFAULT_FROM_DATE, help="Kokkai API from date. Default: 2023-01-01")
    parser.add_argument("--limit", type=int, default=5, help="Supabase legislator sample size when --names is omitted.")
    parser.add_argument("--maximum-records", type=int, default=100, help="Kokkai API maximumRecords per legislator.")
    parser.add_argument("--names", nargs="*", help="Specific legislator names to verify instead of reading Supabase.")
    parser.add_argument("--preview-length", type=int, default=160, help="Speech preview characters per grouped question.")
    parser.add_argument("--sleep", type=float, default=0.4, help="Delay between Kokkai API requests.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv()

    if args.names:
        legislators = [Legislator(id=None, name_kanji=name) for name in args.names]
    else:
        legislators = fetch_supabase_legislators(args.limit)

    if not legislators:
        print("No legislators to verify.", file=sys.stderr)
        return 1

    for index, legislator in enumerate(legislators):
        try:
            result = verify_legislator(
                legislator,
                from_date=args.from_date,
                maximum_records=args.maximum_records,
            )
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"ERROR {legislator.name_kanji}: {exc}", file=sys.stderr)
            continue
        print_result(result, preview_length=args.preview_length)
        if index < len(legislators) - 1:
            time.sleep(args.sleep)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
