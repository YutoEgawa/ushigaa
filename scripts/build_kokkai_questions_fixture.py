from __future__ import annotations

import argparse
import json
import re
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


KOKKAI_API_URL = "https://kokkai.ndl.go.jp/api/speech"
DEFAULT_FROM_DATE = "2023-01-01"
USER_AGENT = "ushigaa-kokkai-fixture/0.1"


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.replace("\u3000", " ")
    return re.sub(r"\s+", " ", value).strip()


def normalize_name(value: str | None) -> str:
    value = clean_text(value)
    value = re.sub(r"\s*\[.*?\]\s*", "", value)
    return value.removesuffix("君").replace(" ", "")


def get_json(url: str, timeout: int = 30) -> Any:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_records(name: str, from_date: str, page_size: int, sleep_seconds: float) -> list[dict[str, Any]]:
    search_speaker = normalize_name(name)
    records: list[dict[str, Any]] = []
    start_record = 1

    while True:
        params = urlencode(
            {
                "speaker": search_speaker,
                "from": from_date,
                "startRecord": str(start_record),
                "maximumRecords": str(page_size),
                "recordPacking": "json",
            }
        )
        data = get_json(f"{KOKKAI_API_URL}?{params}")
        page_records = data.get("speechRecord") or []
        for record in page_records:
            if normalize_name(record.get("speaker")) != search_speaker:
                continue
            if record.get("speakerPosition") is not None:
                continue
            if not clean_text(record.get("speech")):
                continue
            records.append(record)

        next_record = data.get("nextRecordPosition")
        if not next_record or not page_records:
            break
        start_record = int(next_record)
        time.sleep(sleep_seconds)

    return records


def build_groups(records: list[dict[str, Any]], from_date: str) -> dict[str, Any]:
    grouped: OrderedDict[tuple[str, str, str], dict[str, Any]] = OrderedDict()
    sorted_records = sorted(
        records,
        key=lambda record: (
            clean_text(record.get("date")),
            clean_text(record.get("nameOfMeeting")),
            int(record["speechOrder"]) if str(record.get("speechOrder") or "").isdigit() else 0,
        ),
        reverse=True,
    )

    for record in sorted_records:
        date = clean_text(record.get("date"))
        name_of_meeting = clean_text(record.get("nameOfMeeting"))
        speaker = clean_text(record.get("speaker"))
        speech = clean_text(record.get("speech"))
        key = (date, name_of_meeting, speaker)
        group = grouped.setdefault(
            key,
            {
                "date": date,
                "name_of_meeting": name_of_meeting,
                "name_of_house": clean_text(record.get("nameOfHouse")) or None,
                "speaker": speaker,
                "speech_count": 0,
                "speeches": [],
                "source_issue_ids": [],
                "source_speech_ids": [],
            },
        )
        group["speech_count"] += 1
        group["speeches"].append((record.get("speechOrder") or 0, speech))
        append_unique(group["source_issue_ids"], clean_text(record.get("issueID")))
        append_unique(group["source_speech_ids"], clean_text(record.get("speechID")))

    items = []
    for group in grouped.values():
        speeches = [speech for _, speech in sorted(group.pop("speeches"), key=lambda item: int(item[0] or 0))]
        items.append({**group, "speech": "\n\n".join(speeches)})

    return {
        "items": items,
        "count": len(items),
        "from_date": from_date,
        "source_speech_count": len(records),
    }


def append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a frontend fixture from Kokkai API question candidates.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--from-date", default=DEFAULT_FROM_DATE)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--sleep", type=float, default=0.25)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = fetch_records(args.name, args.from_date, args.page_size, args.sleep)
    payload = build_groups(records, args.from_date)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"source_speech_count={payload['source_speech_count']}")
    print(f"grouped_questions={payload['count']}")
    print(f"out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
