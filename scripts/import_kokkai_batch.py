from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import socket
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


FROM_DATE = "2023-01-01"
KOKKAI_API = "https://kokkai.ndl.go.jp/api/speech"
KOKKAI_API_USER_AGENT = "curl/8.7.1"
KOKKAI_PAGE_SIZE = 20
OUT_PATH = Path("data/kokkai_import_last_batch.json")


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key, value)


def clean(value: object) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\u3000", " ")).strip()


def normalize_name(value: object) -> str:
    value = clean(value)
    value = re.sub(r"\s*\[.*?\]\s*", "", value)
    return value.removesuffix("君").replace(" ", "")


def house_matches(legislator_house: object, api_house: object) -> bool:
    expected = {
        "shugiin": "衆議院",
        "sangiin": "参議院",
    }.get(clean(legislator_house))
    return not expected or clean(api_house) == expected


def meeting_topic(name_of_meeting: str) -> str:
    rules = [
        ("本会議", "本会議"),
        ("議院運営", "議院運営"),
        ("予算委員会", "予算"),
        (("決算", "行政監視"), "決算・行政監視"),
        (("財務金融", "財政金融"), "財政・金融"),
        (("外交", "外務", "安全保障", "防衛", "国際", "政府開発援助"), "外交・安全保障"),
        ("厚生労働", "厚生労働"),
        (("こども", "子育て", "若者"), "こども・子育て"),
        ("法務", "法務"),
        (("文教", "文部科学"), "教育・科学"),
        (("経済産業", "資源エネルギー", "原子力"), "経済産業・エネルギー"),
        (("環境", "持続可能"), "環境"),
        ("農林水産", "農林水産"),
        ("国土交通", "国土交通"),
        ("総務", "総務・地方行政"),
        (("地方創生", "地域活性化", "デジタル", "人工知能"), "地方創生・デジタル"),
        ("消費者", "消費者"),
        (("内閣委員会", "国家基本政策"), "内閣・国家基本政策"),
        ("憲法", "憲法"),
        (("政治改革", "政治倫理", "公職選挙", "選挙制度"), "政治改革・選挙"),
        (("災害", "復興"), "災害・復興"),
        (("拉致", "北朝鮮"), "拉致・北朝鮮"),
        (("沖縄", "北方"), "沖縄・北方"),
        ("情報監視", "情報監視"),
        ("懲罰", "議員規律"),
        ("調査会", "調査会"),
    ]
    for patterns, topic in rules:
        if isinstance(patterns, str):
            patterns = (patterns,)
        if any(pattern in name_of_meeting for pattern in patterns):
            return topic
    return "調査会"


class SupabaseRest:
    def __init__(self) -> None:
        supabase_url = os.environ.get("SUPABASE_URL")
        secret_key = os.environ.get("SUPABASE_SECRET_KEY")
        service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        anon_key = os.environ.get("SUPABASE_ANON_KEY")
        if not supabase_url:
            raise RuntimeError("SUPABASE_URL is required.")
        if os.environ.get("GITHUB_ACTIONS") == "true" and not (secret_key or service_role_key):
            raise RuntimeError("SUPABASE_SECRET_KEY or SUPABASE_SERVICE_ROLE_KEY is required for GitHub Actions imports.")
        key = secret_key or service_role_key or anon_key
        if not key:
            raise RuntimeError("SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, or SUPABASE_ANON_KEY is required.")
        self.url = supabase_url.rstrip("/")
        self.key = key

    @property
    def read_headers(self) -> dict[str, str]:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Accept": "application/json",
        }

    @property
    def write_headers(self) -> dict[str, str]:
        return {
            **self.read_headers,
            "Content-Type": "application/json",
        }

    def get(self, path: str, params: dict[str, str]) -> list[dict[str, Any]]:
        request = Request(f"{self.url}/rest/v1/{path}?{urlencode(params)}", headers=self.read_headers)
        last_error: Exception | None = None
        for attempt in range(1, 5):
            try:
                with urlopen(request, timeout=30) as response:
                    return json.loads(response.read().decode("utf-8"))
            except (
                http.client.IncompleteRead,
                http.client.RemoteDisconnected,
                TimeoutError,
                socket.timeout,
            ) as exc:
                last_error = exc
                if attempt == 4:
                    break
                time.sleep(min(2**attempt, 10))
        assert last_error is not None
        raise last_error

    def post(
        self,
        path: str,
        rows: list[dict[str, Any]],
        on_conflict: str,
        *,
        resolution: str = "ignore-duplicates",
    ) -> list[dict[str, Any]]:
        if not rows:
            return []
        request = Request(
            f"{self.url}/rest/v1/{path}?{urlencode({'on_conflict': on_conflict})}",
            method="POST",
            data=json.dumps(rows, ensure_ascii=False).encode("utf-8"),
            headers={
                **self.write_headers,
                "Prefer": f"resolution={resolution},return=representation",
            },
        )
        last_error: Exception | None = None
        for attempt in range(1, 5):
            try:
                with urlopen(request, timeout=60) as response:
                    body = response.read().decode("utf-8")
                    return json.loads(body) if body else []
            except HTTPError as exc:
                print(f"POST error {path} {exc.code}: {exc.read().decode('utf-8')}")
                raise
            except (
                http.client.IncompleteRead,
                http.client.RemoteDisconnected,
                TimeoutError,
                socket.timeout,
            ) as exc:
                last_error = exc
                if attempt == 4:
                    break
                time.sleep(min(2**attempt, 10))
        assert last_error is not None
        raise last_error


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def fetch_json(url: str, attempts: int = 4) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": KOKKAI_API_USER_AGENT, "Accept": "application/json"})
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504}:
                raise
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(min(2**attempt, 10))
        except (
            http.client.IncompleteRead,
            http.client.RemoteDisconnected,
            URLError,
            TimeoutError,
            socket.timeout,
        ) as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(min(2**attempt, 10))
    assert last_error is not None
    raise last_error


def next_legislators(client: SupabaseRest, limit: int) -> list[dict[str, Any]]:
    legislators = client.get(
        "legislators",
        {
            "select": "id,name_kanji,name_kana,house",
            "status": "eq.active",
            "order": "name_kana.asc",
            "limit": "1000",
        },
    )
    statuses = client.get(
        "kokkai_legislator_import_status",
        {"select": "legislator_id", "limit": "1000"},
    )
    done = {row["legislator_id"] for row in statuses}
    return [row for row in legislators if row["id"] not in done][:limit]


def active_legislators(client: SupabaseRest, limit: int | None = None) -> list[dict[str, Any]]:
    params = {
        "select": "id,name_kanji,name_kana,house",
        "status": "eq.active",
        "order": "name_kana.asc",
        "limit": str(limit or 1000),
    }
    return client.get("legislators", params)


def latest_import_from_date(client: SupabaseRest, lookback_days: int) -> str:
    rows = client.get(
        "kokkai_meetings",
        {"select": "date", "order": "date.desc", "limit": "1"},
    )
    if not rows or not rows[0].get("date"):
        return FROM_DATE
    latest_date = parse_date(rows[0]["date"])
    from_date = max(parse_date(FROM_DATE), latest_date - timedelta(days=lookback_days))
    return from_date.isoformat()


def fetch_question_records(
    legislator: dict[str, Any],
    from_date: str,
    sleep_seconds: float,
    page_size: int = KOKKAI_PAGE_SIZE,
) -> list[dict[str, Any]]:
    search_speaker = normalize_name(legislator["name_kanji"])
    records: list[dict[str, Any]] = []
    start_record = 1
    while True:
        url = f"{KOKKAI_API}?" + urlencode(
            {
                "speaker": search_speaker,
                "from": from_date,
                "startRecord": str(start_record),
                "maximumRecords": str(page_size),
                "recordPacking": "json",
            }
        )
        data = fetch_json(url)
        page = data.get("speechRecord") or []
        for record in page:
            if normalize_name(record.get("speaker")) != search_speaker:
                continue
            if not house_matches(legislator.get("house"), record.get("nameOfHouse")):
                continue
            if record.get("speakerPosition") is not None:
                continue
            if not clean(record.get("speech")):
                continue
            records.append({**record, "_legislator_id": legislator["id"]})
        next_record = data.get("nextRecordPosition")
        if not next_record or not page:
            break
        start_record = int(next_record)
        time.sleep(sleep_seconds)
    return records


def build_question_groups(records: list[dict[str, Any]], meeting_map: dict[str, str]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in records:
        issue_id = clean(record.get("issueID"))
        meeting_id = meeting_map.get(issue_id)
        speaker = clean(record.get("speaker"))
        if not meeting_id or not speaker:
            continue
        key = (record["_legislator_id"], meeting_id, speaker)
        group = grouped.setdefault(
            key,
            {
                "legislator_id": record["_legislator_id"],
                "meeting_id": meeting_id,
                "speaker": speaker,
                "speeches": [],
                "source_issue_ids": [],
                "source_speech_ids": [],
                "orders": [],
            },
        )
        speech_id = clean(record.get("speechID"))
        order = record.get("speechOrder")
        speech_order = int(order) if str(order or "").isdigit() else None
        group["speeches"].append((speech_order, speech_id, clean(record.get("speech"))))
        if issue_id and issue_id not in group["source_issue_ids"]:
            group["source_issue_ids"].append(issue_id)
        if speech_id:
            group["source_speech_ids"].append(speech_id)
        if speech_order is not None:
            group["orders"].append(speech_order)

    groups = []
    for group in grouped.values():
        speeches = sorted(group["speeches"], key=lambda row: (row[0] is None, row[0] or 0, row[1]))
        orders = group["orders"]
        groups.append(
            {
                "legislator_id": group["legislator_id"],
                "meeting_id": group["meeting_id"],
                "speaker": group["speaker"],
                "speech_count": len(speeches),
                "speech": "\n\n".join(speech for _, _, speech in speeches if speech),
                "source_issue_ids": group["source_issue_ids"],
                "source_speech_ids": [speech_id for _, speech_id, _ in speeches if speech_id],
                "first_speech_order": min(orders) if orders else None,
                "last_speech_order": max(orders) if orders else None,
            }
        )
    return groups


def import_records(client: SupabaseRest, records: list[dict[str, Any]]) -> tuple[int, int, int]:
    records = dedupe_records(records)
    meetings_by_issue: dict[str, dict[str, Any]] = {}
    for record in records:
        issue_id = clean(record.get("issueID"))
        if issue_id:
            meetings_by_issue[issue_id] = {
                "source_issue_id": issue_id,
                "name_of_house": clean(record.get("nameOfHouse")) or None,
                "name_of_meeting": clean(record.get("nameOfMeeting")),
                "meeting_topic": meeting_topic(clean(record.get("nameOfMeeting"))),
                "date": clean(record.get("date")),
            }

    meetings = list(meetings_by_issue.values())
    for index in range(0, len(meetings), 100):
        client.post(
            "kokkai_meetings",
            meetings[index : index + 100],
            "source_issue_id",
            resolution="merge-duplicates",
        )

    meeting_map: dict[str, str] = {}
    issue_ids = list(meetings_by_issue)
    for index in range(0, len(issue_ids), 80):
        batch = issue_ids[index : index + 80]
        rows = client.get(
            "kokkai_meetings",
            {
                "select": "id,source_issue_id",
                "source_issue_id": "in.(" + ",".join(f'"{value}"' for value in batch) + ")",
                "limit": "1000",
            },
        )
        meeting_map.update({row["source_issue_id"]: row["id"] for row in rows})

    groups = build_question_groups(records, meeting_map)
    speeches = []
    for record in records:
        issue_id = clean(record.get("issueID"))
        speech_id = clean(record.get("speechID"))
        meeting_id = meeting_map.get(issue_id)
        if not issue_id or not speech_id or not meeting_id:
            continue
        order = record.get("speechOrder")
        speeches.append(
            {
                "legislator_id": record["_legislator_id"],
                "meeting_id": meeting_id,
                "source_speech_id": speech_id,
                "source_issue_id": issue_id,
                "speech_order": int(order) if str(order or "").isdigit() else None,
                "speaker": clean(record.get("speaker")),
                "speaker_position": None,
                "speech": clean(record.get("speech")),
            }
        )
    for index in range(0, len(speeches), 50):
        client.post(
            "kokkai_speeches",
            speeches[index : index + 50],
            "source_speech_id",
            resolution="merge-duplicates",
        )
    for index in range(0, len(groups), 50):
        client.post(
            "kokkai_question_groups",
            groups[index : index + 50],
            "legislator_id,meeting_id,speaker",
            resolution="merge-duplicates",
        )
    return len(meetings), len(speeches), len(groups)


def dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for record in records:
        speech_id = clean(record.get("speechID"))
        if speech_id and speech_id in seen:
            continue
        if speech_id:
            seen.add(speech_id)
        deduped.append(record)
    return deduped


def update_import_status(
    client: SupabaseRest,
    legislator: dict[str, Any],
    from_date: str,
    *,
    speech_count: int,
    group_count: int,
    status: str,
    error_message: str | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    client.post(
        "kokkai_legislator_import_status",
        [
            {
                "legislator_id": legislator["id"],
                "from_date": from_date,
                "checked_at": now,
                "speech_count": speech_count,
                "group_count": group_count,
                "status": status,
                "error_message": error_message,
                "updated_at": now,
            }
        ],
        "legislator_id",
        resolution="merge-duplicates",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Kokkai question candidates.")
    parser.add_argument("--mode", choices=("next", "delta"), default="next")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--from-date")
    parser.add_argument("--lookback-days", type=int, default=14)
    parser.add_argument("--page-size", type=int, default=KOKKAI_PAGE_SIZE)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv()
    client = SupabaseRest()
    from_date = args.from_date or (latest_import_from_date(client, args.lookback_days) if args.mode == "delta" else FROM_DATE)
    legislators = active_legislators(client, args.limit if args.limit > 0 else None) if args.mode == "delta" else next_legislators(client, args.limit)
    print("mode=", args.mode)
    print("from_date=", from_date)
    print("batch_legislators=", len(legislators), [row["name_kanji"] for row in legislators])

    all_records: list[dict[str, Any]] = []
    per_member = []
    error_count = 0
    for legislator in legislators:
        try:
            records = fetch_question_records(legislator, from_date, args.sleep, args.page_size)
            all_records.extend(records)
            group_count = len({(record["_legislator_id"], clean(record.get("issueID")), clean(record.get("speaker"))) for record in records})
            update_import_status(
                client,
                legislator,
                from_date,
                speech_count=len(records),
                group_count=group_count,
                status="success",
            )
            error_message = None
        except Exception as exc:
            records = []
            group_count = 0
            error_count += 1
            error_message = str(exc)
            update_import_status(
                client,
                legislator,
                from_date,
                speech_count=0,
                group_count=0,
                status="error",
                error_message=error_message,
            )
        per_member.append(
            {
                "legislator_id": legislator["id"],
                "name_kanji": legislator["name_kanji"],
                "speech_count": len(records),
                "group_count": group_count,
                "error_message": error_message,
            }
        )
        print(legislator["name_kanji"], len(records), error_message or "")

    meeting_count, speech_count, group_count = import_records(client, all_records)
    report = {
        "mode": args.mode,
        "from_date": from_date,
        "lookback_days": args.lookback_days,
        "page_size": args.page_size,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "members": per_member,
        "total_records": len(all_records),
        "meetings": meeting_count,
        "speeches_prepared": speech_count,
        "groups_prepared": group_count,
        "error_count": error_count,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("total_records=", len(all_records))
    print("meetings=", meeting_count)
    print("speeches_prepared=", speech_count)
    print("groups_prepared=", group_count)
    print("error_count=", error_count)
    print("report=", args.out)
    if error_count:
        print(f"failed_legislators={error_count}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
