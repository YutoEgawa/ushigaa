from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from app.config import Settings


LEGISLATOR_SELECT = ",".join(
    [
        "id",
        "name_kanji",
        "name_kana",
        "house",
        "photo_url",
        "party_name",
        "party_short",
        "party_color",
        "district_name",
        "district_type",
        "block_name",
        "election_year",
        "election_type",
        "birth_date",
        "birth_date_precision",
        "birth_date_source_url",
        "election_count",
        "election_count_note",
        "election_count_source_url",
        "career_summary",
        "career_source_url",
        "profile_source_url",
        "profile_source_type",
        "profile_source_checked_at",
    ]
)


class SupabaseClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.headers = {
            "apikey": settings.supabase_anon_key,
            "Authorization": f"Bearer {settings.supabase_anon_key}",
            "Accept": "application/json",
        }

    async def get(self, path: str, params: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], int | None]:
        import httpx

        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            response = await client.get(
                f"{self.settings.rest_url}/{path.lstrip('/')}",
                headers={**self.headers, "Prefer": "count=exact"},
                params=params,
            )
            response.raise_for_status()
            return response.json(), parse_content_range_count(response.headers.get("content-range"))


def parse_content_range_count(value: str | None) -> int | None:
    if not value or "/" not in value:
        return None
    total = value.rsplit("/", 1)[-1]
    if total == "*":
        return None
    try:
        return int(total)
    except ValueError:
        return None


def build_legislator_params(
    *,
    house: str | None,
    party: str | None,
    district: str | None,
    q: str | None,
    limit: int,
    offset: int,
) -> dict[str, str | int]:
    params: dict[str, str | int] = {
        "select": LEGISLATOR_SELECT,
        "order": "name_kana.asc",
        "limit": limit,
        "offset": offset,
    }
    if house:
        params["house"] = f"eq.{house}"
    if party:
        params["party_name"] = f"eq.{party}"
    if district:
        params["district_name"] = f"eq.{district}"
    if q:
        pattern = f"*{q}*"
        params["or"] = (
            f"(name_kanji.ilike.{pattern},"
            f"name_kana.ilike.{pattern},"
            f"party_name.ilike.{pattern},"
            f"district_name.ilike.{pattern})"
        )
    return params
