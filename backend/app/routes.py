import random
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import Settings, get_settings
from app.email_sender import EmailNotConfiguredError, EmailSendError, send_contact_email
from app.models import (
    ContactRequest,
    ContactResponse,
    District,
    KokkaiQuestion,
    KokkaiQuestionListResponse,
    KokkaiTopicRanking,
    KokkaiTopicRankingResponse,
    KokkaiTopicTopRanking,
    KokkaiTopicTopRankingItem,
    KokkaiTopicTopRankingResponse,
    LegislatorListResponse,
    LegislatorSummary,
    Party,
    PowerMapHouse,
    PowerMapResponse,
    PowerMapSegment,
)
from app.supabase_client import LEGISLATOR_SELECT, SupabaseClient, build_legislator_params

router = APIRouter()

GAUGE_COLORS = [
    "#38D5FF",
    "#A7F83B",
    "#FFBE3D",
    "#B985FF",
    "#FF6B45",
    "#35E0A1",
    "#6F8CFF",
]


def get_supabase(settings: Annotated[Settings, Depends(get_settings)]) -> SupabaseClient:
    return SupabaseClient(settings)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/legislators", response_model=LegislatorListResponse)
async def list_legislators(
    supabase: Annotated[SupabaseClient, Depends(get_supabase)],
    house: Annotated[str | None, Query(pattern="^(shugiin|sangiin)$")] = None,
    party: str | None = None,
    district: str | None = None,
    q: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
    question_count_min: Annotated[int | None, Query(ge=0)] = None,
    question_count_max: Annotated[int | None, Query(ge=0)] = None,
    government_role: Annotated[
        str | None,
        Query(pattern="^(has|none|prime_minister|minister|senior_vice_minister|parliamentary_vice_minister)$"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LegislatorListResponse:
    if question_count_min is not None or question_count_max is not None or government_role is not None:
        return await list_legislators_with_derived_filters(
            supabase=supabase,
            house=house,
            party=party,
            district=district,
            q=q,
            question_count_min=question_count_min,
            question_count_max=question_count_max,
            government_role=government_role,
            limit=limit,
            offset=offset,
        )

    params = build_legislator_params(
        house=house,
        party=party,
        district=district,
        q=q,
        limit=limit,
        offset=offset,
    )
    rows, count = await supabase.get("active_legislators", params)
    return LegislatorListResponse(
        items=[LegislatorSummary.model_validate(row) for row in rows],
        limit=limit,
        offset=offset,
        count=count,
    )


async def list_legislators_with_derived_filters(
    *,
    supabase: SupabaseClient,
    house: str | None,
    party: str | None,
    district: str | None,
    q: str | None,
    question_count_min: int | None,
    question_count_max: int | None,
    government_role: str | None,
    limit: int,
    offset: int,
) -> LegislatorListResponse:
    params = build_legislator_params(
        house=house,
        party=party,
        district=district,
        q=q,
        limit=1000,
        offset=0,
    )
    rows, _ = await supabase.get("active_legislators", params)
    counts = await load_question_counts(supabase)
    role_flags = await load_government_role_flags(supabase)
    min_count = question_count_min if question_count_min is not None else 0
    max_count = question_count_max if question_count_max is not None else 10**9
    filtered_rows = []
    for row in rows:
        legislator_id = str(row.get("id"))
        question_count = counts.get(legislator_id, 0)
        flags = role_flags.get(legislator_id, {})
        has_role = bool(flags.get("has_executive_government_experience"))
        if government_role in {
            "prime_minister",
            "minister",
            "senior_vice_minister",
            "parliamentary_vice_minister",
        } and not bool(flags.get(f"has_{government_role}_experience")):
            continue
        if government_role == "has" and not has_role:
            continue
        if government_role == "none" and has_role:
            continue
        if min_count <= question_count <= max_count:
            filtered_rows.append(
                {
                    **row,
                    **flags,
                    "kokkai_question_count": question_count,
                    "has_executive_government_experience": has_role,
                }
            )

    filtered_rows.sort(key=lambda row: str(row.get("name_kana") or ""))
    page_rows = filtered_rows[offset : offset + limit]
    return LegislatorListResponse(
        items=[LegislatorSummary.model_validate(row) for row in page_rows],
        limit=limit,
        offset=offset,
        count=len(filtered_rows),
    )


async def load_question_counts(supabase: SupabaseClient) -> dict[str, int]:
    counts: dict[str, int] = {}
    limit = 1000
    offset = 0
    while True:
        rows, _ = await supabase.get(
            "kokkai_question_groups",
            {
                "select": "legislator_id",
                "limit": limit,
                "offset": offset,
            },
        )
        for row in rows:
            legislator_id = row.get("legislator_id")
            if isinstance(legislator_id, str):
                counts[legislator_id] = counts.get(legislator_id, 0) + 1
        if len(rows) < limit:
            break
        offset += limit
    return counts


async def load_all_rows(
    supabase: SupabaseClient,
    table: str,
    params: dict[str, object],
    *,
    limit: int = 1000,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    offset = 0
    while True:
        page, _ = await supabase.get(
            table,
            {
                **params,
                "limit": limit,
                "offset": offset,
            },
        )
        rows.extend(page)
        if len(page) < limit:
            break
        offset += limit
    return rows


async def load_topic_question_counts(
    supabase: SupabaseClient,
    from_date: date,
) -> dict[str, dict[str, int]]:
    topic_counts: dict[str, dict[str, int]] = {}
    if from_date == date(2023, 1, 1):
        rows = await load_all_rows(
            supabase,
            "kokkai_question_topic_counts",
            {"select": "legislator_id,meeting_topic,question_count"},
        )
        for row in rows:
            legislator_id = row.get("legislator_id")
            topic = row.get("meeting_topic")
            count = row.get("question_count")
            if not isinstance(legislator_id, str):
                continue
            if not isinstance(topic, str) or not topic:
                topic = "調査会"
            if not isinstance(count, int):
                continue
            topic_counts.setdefault(topic, {})
            topic_counts[topic][legislator_id] = count
        return topic_counts

    question_rows = await load_all_rows(
        supabase,
        "kokkai_question_group_rows",
        {
            "select": "legislator_id,meeting_topic",
            "date": f"gte.{from_date.isoformat()}",
        },
    )
    for row in question_rows:
        legislator_id = row.get("legislator_id")
        if not isinstance(legislator_id, str):
            continue
        topic = row.get("meeting_topic")
        if not isinstance(topic, str) or not topic:
            topic = "調査会"
        topic_counts.setdefault(topic, {})
        topic_counts[topic][legislator_id] = topic_counts[topic].get(legislator_id, 0) + 1
    return topic_counts


async def load_government_role_flags(supabase: SupabaseClient) -> dict[str, dict[str, bool]]:
    flags: dict[str, dict[str, bool]] = {}
    limit = 1000
    offset = 0
    while True:
        rows, _ = await supabase.get(
            "legislator_government_role_flags",
            {
                "select": (
                    "legislator_id,has_prime_minister_experience,"
                    "has_minister_experience,"
                    "has_senior_vice_minister_experience,"
                    "has_parliamentary_vice_minister_experience,"
                    "has_executive_government_experience"
                ),
                "limit": limit,
                "offset": offset,
            },
        )
        for row in rows:
            legislator_id = row.get("legislator_id")
            if isinstance(legislator_id, str):
                flags[legislator_id] = {
                    "has_prime_minister_experience": bool(
                        row.get("has_prime_minister_experience")
                    ),
                    "has_minister_experience": bool(row.get("has_minister_experience")),
                    "has_senior_vice_minister_experience": bool(
                        row.get("has_senior_vice_minister_experience")
                    ),
                    "has_parliamentary_vice_minister_experience": bool(
                        row.get("has_parliamentary_vice_minister_experience")
                    ),
                    "has_executive_government_experience": bool(
                        row.get("has_executive_government_experience")
                    ),
                }
        if len(rows) < limit:
            break
        offset += limit
    return flags


@router.get("/legislators/{legislator_id}", response_model=LegislatorSummary)
async def get_legislator(
    legislator_id: str,
    supabase: Annotated[SupabaseClient, Depends(get_supabase)],
) -> LegislatorSummary:
    rows, _ = await supabase.get(
        "active_legislators",
        {"select": "*", "id": f"eq.{legislator_id}", "limit": 1},
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Legislator not found")
    return LegislatorSummary.model_validate(rows[0])


@router.get("/legislators/{legislator_id}/questions", response_model=KokkaiQuestionListResponse)
async def list_legislator_questions(
    legislator_id: str,
    supabase: Annotated[SupabaseClient, Depends(get_supabase)],
    from_date: Annotated[date, Query(alias="from")] = date(2023, 1, 1),
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> KokkaiQuestionListResponse:
    rows, count = await supabase.get(
        "kokkai_question_group_rows",
        {
            "select": (
                "id,legislator_id,date,name_of_house,name_of_meeting,meeting_topic,speaker,"
                "speech_count,speech,source_issue_ids,source_speech_ids"
            ),
            "legislator_id": f"eq.{legislator_id}",
            "date": f"gte.{from_date.isoformat()}",
            "order": "date.desc,name_of_meeting.asc",
            "limit": limit,
            "offset": offset,
        },
    )
    questions = [KokkaiQuestion.model_validate(row) for row in rows]
    return KokkaiQuestionListResponse(
        items=questions,
        count=count if count is not None else len(questions),
        from_date=from_date,
    )


@router.get(
    "/legislators/{legislator_id}/question-topic-rankings",
    response_model=KokkaiTopicRankingResponse,
)
async def list_legislator_question_topic_rankings(
    legislator_id: str,
    supabase: Annotated[SupabaseClient, Depends(get_supabase)],
    from_date: Annotated[date, Query(alias="from")] = date(2023, 1, 1),
) -> KokkaiTopicRankingResponse:
    legislators = await load_all_rows(
        supabase,
        "active_legislators",
        {"select": "id,name_kanji,name_kana,party_name"},
    )
    legislator_lookup = {
        str(row.get("id")): row
        for row in legislators
        if isinstance(row.get("id"), str)
    }
    if legislator_id not in legislator_lookup:
        raise HTTPException(status_code=404, detail="Legislator not found")

    topic_counts = await load_topic_question_counts(supabase, from_date)

    rankings: list[KokkaiTopicRanking] = []
    for topic, counts in topic_counts.items():
        current_count = counts.get(legislator_id, 0)
        if current_count <= 0:
            continue
        ranked_counts = sorted(
            counts.items(),
            key=lambda item: (-item[1], str(legislator_lookup.get(item[0], {}).get("name_kana") or "")),
        )
        ranks: dict[str, int] = {}
        previous_count: int | None = None
        current_rank = 0
        for index, (ranked_legislator_id, count) in enumerate(ranked_counts, start=1):
            if count != previous_count:
                current_rank = index
                previous_count = count
            ranks[ranked_legislator_id] = current_rank

        rankings.append(
            KokkaiTopicRanking(
                topic=topic,
                current_count=current_count,
                current_rank=ranks[legislator_id],
                total_legislators=len(counts),
            )
        )

    rankings.sort(key=lambda item: (-item.current_count, item.topic))
    return KokkaiTopicRankingResponse(items=rankings, from_date=from_date)


@router.get("/kokkai/question-topic-rankings", response_model=KokkaiTopicTopRankingResponse)
async def list_question_topic_top_rankings(
    supabase: Annotated[SupabaseClient, Depends(get_supabase)],
    from_date: Annotated[date, Query(alias="from")] = date(2023, 1, 1),
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> KokkaiTopicTopRankingResponse:
    legislators = await load_all_rows(
        supabase,
        "active_legislators",
        {"select": "id,name_kanji,name_kana,party_name"},
    )
    legislator_lookup = {
        str(row.get("id")): row
        for row in legislators
        if isinstance(row.get("id"), str)
    }
    topic_counts = await load_topic_question_counts(supabase, from_date)
    rankings: list[KokkaiTopicTopRanking] = []
    for topic, counts in topic_counts.items():
        ranked_counts = sorted(
            counts.items(),
            key=lambda item: (-item[1], str(legislator_lookup.get(item[0], {}).get("name_kana") or "")),
        )
        items: list[KokkaiTopicTopRankingItem] = []
        previous_count: int | None = None
        current_rank = 0
        for index, (legislator_id, count) in enumerate(ranked_counts, start=1):
            if count != previous_count:
                current_rank = index
                previous_count = count
            if len(items) >= limit:
                break
            legislator = legislator_lookup.get(legislator_id)
            if not legislator:
                continue
            name = legislator.get("name_kanji")
            if not isinstance(name, str):
                continue
            party_name = legislator.get("party_name")
            items.append(
                KokkaiTopicTopRankingItem(
                    legislator_id=legislator_id,
                    name_kanji=name,
                    party_name=party_name if isinstance(party_name, str) else None,
                    question_count=count,
                    rank=current_rank,
                )
            )
        rankings.append(
            KokkaiTopicTopRanking(
                topic=topic,
                total_legislators=len(counts),
                items=items,
            )
        )

    rankings.sort(key=lambda item: item.topic)
    return KokkaiTopicTopRankingResponse(items=rankings, from_date=from_date)


@router.get("/parties", response_model=list[Party])
async def list_parties(
    supabase: Annotated[SupabaseClient, Depends(get_supabase)],
    house: Annotated[str | None, Query(pattern="^(shugiin|sangiin)$")] = None,
) -> list[Party]:
    rows, _ = await supabase.get(
        "parties",
        {
            "select": (
                "id,name,name_short,color_hex,alignment,alignment_rank,"
                "alignment_rank_member_count,alignment_basis,alignment_source_url,"
                "alignment_source_checked_at"
            ),
            "order": "alignment.asc,alignment_rank.asc,name.asc",
        },
    )
    if house:
        member_rows, _ = await supabase.get(
            "active_legislators",
            {"select": "party_name", "house": f"eq.{house}", "limit": 1000},
        )
        rows = apply_house_alignment_ranks(rows, member_rows)
    return [Party.model_validate(row) for row in rows]


def apply_house_alignment_ranks(
    parties: list[dict[str, object]],
    members: list[dict[str, object]],
) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    for member in members:
        party_name = member.get("party_name")
        if isinstance(party_name, str) and party_name:
            counts[party_name] = counts.get(party_name, 0) + 1

    ranked_rows: list[dict[str, object]] = []
    for party in parties:
        name = party.get("name")
        if not isinstance(name, str) or counts.get(name, 0) <= 0:
            continue
        ranked_rows.append({**party, "alignment_rank_member_count": counts[name]})

    group_order = {"ruling": 0, "opposition": 1, "other": 2}
    ranked_rows.sort(
        key=lambda row: (
            group_order.get(str(row.get("alignment")), 99),
            -int(row.get("alignment_rank_member_count") or 0),
            str(row.get("name") or ""),
        )
    )

    current_alignment: object = object()
    rank = 0
    for row in ranked_rows:
        alignment = row.get("alignment")
        if alignment != current_alignment:
            current_alignment = alignment
            rank = 1
        else:
            rank += 1
        row["alignment_rank"] = rank

    return ranked_rows


@router.get("/power-map", response_model=PowerMapResponse)
async def power_map(
    supabase: Annotated[SupabaseClient, Depends(get_supabase)],
) -> PowerMapResponse:
    parties, members = await load_power_map_sources(supabase)
    return PowerMapResponse(
        shugiin=build_power_map_house(parties, members, "shugiin", "衆議院"),
        sangiin=build_power_map_house(parties, members, "sangiin", "参議院"),
    )


async def load_power_map_sources(supabase: SupabaseClient) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    parties, _ = await supabase.get(
        "parties",
        {
            "select": "name,name_short,color_hex,alignment,alignment_rank,alignment_rank_member_count",
            "order": "alignment.asc,alignment_rank.asc,name.asc",
        },
    )
    members, _ = await supabase.get(
        "active_legislators",
        {"select": "house,party_name", "limit": 1000},
    )
    return parties, members


def build_power_map_house(parties: list[dict[str, object]], members: list[dict[str, object]], house: str, title: str) -> PowerMapHouse:
    house_members = [member for member in members if member.get("house") == house]
    ranked_parties = apply_house_alignment_ranks(parties, house_members)
    party_map = {str(party.get("name")): party for party in ranked_parties if party.get("name")}

    counts: dict[str, int] = {}
    for member in house_members:
        party_name = member.get("party_name")
        label = party_name if isinstance(party_name, str) and party_name else "その他"
        counts[label] = counts.get(label, 0) + 1

    segments = sorted(
        (
            build_power_map_segment(label, seats, party_map.get(label))
            for label, seats in counts.items()
        ),
        key=power_map_sort_key,
    )
    colored_segments = [
        segment.model_copy(
            update={
                "color": "#65708A"
                if segment.alignment == "other"
                else GAUGE_COLORS[index % len(GAUGE_COLORS)]
            }
        )
        for index, segment in enumerate(segments)
    ]
    ruling_seats = sum(segment.seats for segment in colored_segments if segment.alignment == "ruling")
    return PowerMapHouse(
        title=title,
        totalSeats=len(house_members),
        rulingSeats=ruling_seats,
        segments=colored_segments,
    )


def build_power_map_segment(label: str, seats: int, party: dict[str, object] | None) -> PowerMapSegment:
    alignment = (
        str(party.get("alignment"))
        if party and party.get("alignment")
        else ("other" if label == "無所属" else "opposition")
    )
    return PowerMapSegment(
        label=label,
        seats=seats,
        color="#65708A",
        alignment=alignment,
        alignmentRank=int(party.get("alignment_rank") or 999) if party else 999,
        memberCount=int(party.get("alignment_rank_member_count") or seats) if party else seats,
    )


def power_map_sort_key(segment: PowerMapSegment) -> tuple[int, int, int, str]:
    group_order = {"ruling": 0, "opposition": 1, "other": 2}
    return (
        group_order.get(segment.alignment, 99),
        segment.alignmentRank,
        -segment.seats,
        segment.label,
    )


@router.get("/featured-freshmen", response_model=list[LegislatorSummary])
async def featured_freshmen(
    supabase: Annotated[SupabaseClient, Depends(get_supabase)],
    limit: Annotated[int, Query(ge=1, le=12)] = 3,
) -> list[LegislatorSummary]:
    rows, _ = await supabase.get(
        "active_legislators",
        {
            "select": LEGISLATOR_SELECT,
            "election_count": "eq.1",
            "order": "name_kana.asc",
            "limit": 1000,
        },
    )
    if not rows:
        return []
    selected_rows = random.sample(rows, k=min(limit, len(rows)))
    return [LegislatorSummary.model_validate(row) for row in selected_rows]


@router.get("/districts", response_model=list[District])
async def list_districts(
    supabase: Annotated[SupabaseClient, Depends(get_supabase)],
    house: Annotated[str | None, Query(pattern="^(shugiin|sangiin)$")] = None,
) -> list[District]:
    params: dict[str, str] = {"select": "id,house,type,name,block_name", "order": "house.asc,name.asc"}
    if house:
        params["house"] = f"eq.{house}"
    rows, _ = await supabase.get("districts", params)
    return [District.model_validate(row) for row in rows]


@router.post("/contact", response_model=ContactResponse)
async def send_contact(
    payload: ContactRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ContactResponse:
    try:
        send_contact_email(settings, payload)
    except EmailNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail="Contact email is not configured") from exc
    except EmailSendError as exc:
        raise HTTPException(status_code=502, detail="Failed to send contact email") from exc
    return ContactResponse(status="sent")
