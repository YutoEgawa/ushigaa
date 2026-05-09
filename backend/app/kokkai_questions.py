from __future__ import annotations

from app.models import KokkaiQuestion


def build_question_groups(rows: list[dict[str, object]]) -> list[KokkaiQuestion]:
    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in rows:
        row_date = str(row.get("date") or "")
        name_of_meeting = str(row.get("name_of_meeting") or "")
        speaker = str(row.get("speaker") or "")
        speech = str(row.get("speech") or "").strip()
        if not row_date or not name_of_meeting or not speaker or not speech:
            continue
        key = (row_date, name_of_meeting, speaker)
        group = grouped.setdefault(
            key,
            {
                "date": row_date,
                "name_of_meeting": name_of_meeting,
                "name_of_house": row.get("name_of_house"),
                "speaker": speaker,
                "speeches": [],
                "source_issue_ids": [],
                "source_speech_ids": [],
            },
        )
        group["speeches"].append(speech)
        append_unique(group["source_issue_ids"], row.get("source_issue_id"))
        append_unique(group["source_speech_ids"], row.get("source_speech_id"))

    questions = [
        KokkaiQuestion(
            date=group["date"],
            name_of_meeting=str(group["name_of_meeting"]),
            name_of_house=str(group["name_of_house"]) if group.get("name_of_house") else None,
            speaker=str(group["speaker"]),
            speech_count=len(group["speeches"]),
            speech="\n\n".join(str(speech) for speech in group["speeches"]),
            source_issue_ids=[str(value) for value in group["source_issue_ids"]],
            source_speech_ids=[str(value) for value in group["source_speech_ids"]],
        )
        for group in grouped.values()
    ]
    questions.sort(key=lambda item: (item.date, item.name_of_meeting), reverse=True)
    return questions


def append_unique(values: list[object], value: object) -> None:
    if value and value not in values:
        values.append(value)
