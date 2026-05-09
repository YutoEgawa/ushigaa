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
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LegislatorListResponse:
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
                "id,legislator_id,date,name_of_house,name_of_meeting,speaker,"
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
