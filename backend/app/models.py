from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class LegislatorSummary(BaseModel):
    id: str
    name_kanji: str
    name_kana: str
    house: str
    photo_url: str | None = None
    birth_date: date | None = None
    birth_date_precision: str | None = None
    birth_date_source_url: str | None = None
    election_count: int | None = None
    election_count_note: str | None = None
    election_count_source_url: str | None = None
    career_summary: str | None = None
    career_source_url: str | None = None
    profile_source_url: str | None = None
    profile_source_type: str | None = None
    profile_source_checked_at: date | None = None
    party_name: str | None = None
    party_short: str | None = None
    party_color: str | None = None
    district_name: str | None = None
    district_type: str | None = None
    block_name: str | None = None
    election_year: int | None = None
    election_type: str | None = None


class LegislatorListResponse(BaseModel):
    items: list[LegislatorSummary]
    limit: int
    offset: int
    count: int | None = Field(default=None, description="Exact count when Supabase returns it")


class Party(BaseModel):
    id: str
    name: str
    name_short: str | None = None
    color_hex: str | None = None
    alignment: str | None = None
    alignment_rank: int | None = None
    alignment_rank_member_count: int | None = None
    alignment_basis: str | None = None
    alignment_source_url: str | None = None
    alignment_source_checked_at: date | None = None


class District(BaseModel):
    id: str
    house: str
    type: str
    name: str
    block_name: str | None = None


class PowerMapSegment(BaseModel):
    label: str
    seats: int
    color: str
    alignment: str
    alignmentRank: int
    memberCount: int


class PowerMapHouse(BaseModel):
    title: str
    totalSeats: int
    rulingSeats: int
    segments: list[PowerMapSegment]


class PowerMapResponse(BaseModel):
    shugiin: PowerMapHouse
    sangiin: PowerMapHouse


class ContactRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    organization: str | None = Field(default=None, max_length=160)
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    type: Literal["wrong-info", "improvement", "other"]
    detail: str = Field(min_length=1, max_length=5000)


class ContactResponse(BaseModel):
    status: Literal["sent"]
