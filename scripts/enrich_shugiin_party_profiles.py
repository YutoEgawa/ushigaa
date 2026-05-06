from __future__ import annotations

import json
import argparse
import re
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, unquote, urljoin, urlparse
from urllib.request import Request, urlopen

from lxml import html

sys.path.insert(0, str(Path(__file__).resolve().parent))
from enrich_legislator_profiles import clean_text, normalize_name, parse_birth_date, sql_literal


OUT_DIR = Path("data")
SHUGIIN_MEMBERS_PATH = OUT_DIR / "shugiin_members.json"
OUT_JSON = OUT_DIR / "shugiin_party_profile_enrichment.json"
OUT_SQL = OUT_DIR / "enrich_shugiin_party_profiles.sql"
OUT_UNRESOLVED = OUT_DIR / "shugiin_party_profile_unresolved.json"

DDG_URL = "https://duckduckgo.com/html/?q={query}"
JIMIN_MEMBER_JSON = "https://www.jimin.jp/member/data/member.json"
ISHIN_SHUGIIN_URL = "https://o-ishin.jp/member/shugiin/"
KOKUMIN_MEMBER_URL = "https://new-kokumin.jp/member"
SANSEITO_MEMBER_JSON = "https://sanseito.jp/nppoj/wp-content/themes/wp_310/member_for_newpage.json?20260503"
SANSEITO_CANDIDATE_JSON = "https://sanseito.jp/2020/wp-content/themes/twentynineteen/member.json?20260413"
JCP_SHUGIIN_URL = "https://www.jcp.or.jp/diet_member/house/hor/"
CRAJ_MEMBERS_URL = "https://craj.jp/members/"
TEAM_MIRAI_SHUGIIN_URL = "https://team-mir.ai/election/shugiin-2026"

PARTY_DOMAINS = {
    "自由民主党": ["www.jimin.jp"],
    "日本維新の会": ["o-ishin.jp"],
    "国民民主党": ["new-kokumin.jp"],
    "国民民主党・無所属クラブ": ["new-kokumin.jp"],
    "国民民主党・新緑風会": ["new-kokumin.jp"],
    "参政党": ["sanseito.jp"],
    "日本共産党": ["www.jcp.or.jp"],
    "チームみらい": ["team-mir.ai"],
    "チームみらい・無所属": ["team-mir.ai"],
    # The local source currently stores a Diet caucus name here. Search likely
    # party domains explicitly, but only official party pages are auto-imported.
    "中道改革連合・無所属": ["craj.jp"],
}

PARTY_DOMAIN_TO_NAME = {
    "www.jimin.jp": "自由民主党",
    "jimin.jp": "自由民主党",
    "o-ishin.jp": "日本維新の会",
    "new-kokumin.jp": "国民民主党",
    "sanseito.jp": "参政党",
    "www.jcp.or.jp": "日本共産党",
    "jcp.or.jp": "日本共産党",
    "team-mir.ai": "チームみらい",
    "craj.jp": "中道改革連合",
    "cdp-japan.jp": "立憲民主党",
    "www.komei.or.jp": "公明党",
    "komei.or.jp": "公明党",
}


def canonical_party_name(name: str) -> str:
    if name in {"国民民主党・無所属クラブ", "国民民主党・新緑風会"}:
        return "国民民主党"
    if name == "チームみらい・無所属":
        return "チームみらい"
    return name


@dataclass(frozen=True)
class PartyProfileEnrichment:
    name_kanji: str
    name_kana: str
    house: str
    party_name: str
    birth_date: str | None
    birth_date_precision: str | None
    birth_date_source_url: str | None
    career_summary: str | None
    career_source_url: str | None
    profile_source_url: str
    profile_source_type: str
    profile_source_checked_at: str


def fetch(url: str) -> bytes:
    if url in _FETCH_CACHE:
        return _FETCH_CACHE[url]
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; kokkai-giin-db/0.1)"})
    with urlopen(req, timeout=25) as response:
        body = response.read()
    _FETCH_CACHE[url] = body
    return body


_FETCH_CACHE: dict[str, bytes] = {}


def decode_result_url(value: str) -> str:
    if value.startswith("//"):
        value = "https:" + value
    parsed = urlparse(value)
    qs = parse_qs(parsed.query)
    if "uddg" in qs:
        return unquote(qs["uddg"][0])
    return value


def search_urls(query: str, limit: int = 5) -> list[str]:
    url = DDG_URL.format(query=quote(query))
    try:
        doc = html.fromstring(fetch(url))
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"warn: search failed {query}: {exc}")
        return []
    urls: list[str] = []
    for href in doc.xpath('//a[contains(@class, "result__a")]/@href'):
        resolved = decode_result_url(href)
        if resolved.startswith("http") and resolved not in urls:
            urls.append(resolved)
        if len(urls) >= limit:
            break
    return urls


def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def is_official_party_url(url: str, allowed_domains: list[str]) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == domain or host.endswith("." + domain) for domain in allowed_domains)


def page_contains_name(text: str, name: str, kana: str | None = None) -> bool:
    compact_text = re.sub(r"\s+", "", text)
    compact_name = normalize_name(name)
    compact_kana = normalize_name(kana or "")
    if compact_name in compact_text or bool(compact_kana and compact_kana in compact_text):
        return True
    name_parts = name.split()
    kana_parts = (kana or "").split()
    if len(name_parts) >= 2 and len(kana_parts) >= 2:
        mixed = normalize_name(name_parts[0] + kana_parts[-1])
        return mixed in compact_text
    return False


def career_from_lines(lines: list[str]) -> str | None:
    markers = ["経歴等", "経歴", "略歴", "プロフィール", "Message"]
    stop_markers = [
        "生年月日",
        " X ",
        "Tweets by",
        "facebook",
        "事務所",
        "地元事務所",
        "国会事務所",
        "関連ニュース",
        "もっと見る",
        "お問い合わせ",
        "SNS",
        "リンク",
        "シェアする",
        "国民民主党公式SNS",
        "学歴",
        "議員会館",
        "電話：",
        "FAX：",
        "専門性",
        "趣味",
    ]
    for marker in markers:
        for index, line in reversed(list(enumerate(lines))):
            if line == marker or line.startswith(marker + " ") or f" {marker} " in line or marker in line:
                collected: list[str] = []
                if line.startswith(marker + " "):
                    inline = line.removeprefix(marker).strip()
                elif f" {marker} " in line:
                    inline = line.rsplit(marker, 1)[1].strip()
                elif marker in line and line != marker:
                    inline = line.rsplit(marker, 1)[1].strip()
                else:
                    inline = ""
                stop_indexes = [inline.find(stop) for stop in stop_markers if inline.find(stop) >= 0]
                if stop_indexes:
                    inline = inline[: min(stop_indexes)].strip()
                if inline:
                    collected.append(inline)
                for candidate in lines[index + 1 : index + 25]:
                    if any(candidate.startswith(stop) for stop in stop_markers):
                        break
                    if candidate and candidate not in markers:
                        collected.append(candidate)
                summary = clean_text(" ".join(collected))
                if len(summary) >= 20:
                    return summary[:1800]

    joined = clean_text(" ".join(lines))
    birth = parse_birth_date(joined)
    if birth:
        birth_text_index = joined.find("生まれ")
        if birth_text_index >= 0:
            return joined[birth_text_index : birth_text_index + 900]
    return None


def parse_party_profile(url: str, body: bytes, member: dict[str, str], party_name: str) -> PartyProfileEnrichment | None:
    doc = html.fromstring(body)
    lines = [clean_text(line) for line in doc.text_content().splitlines()]
    lines = [line for line in lines if line]
    full_text = clean_text(" ".join(lines))
    if not page_contains_name(full_text, member["name_kanji"], member.get("name_kana")):
        return None

    birth = labeled_birth_date(lines) or parse_birth_date(full_text)
    career_summary = career_from_lines(lines)
    if not birth and not career_summary:
        return None

    return PartyProfileEnrichment(
        name_kanji=member["name_kanji"],
        name_kana=member["name_kana"],
        house="shugiin",
        party_name=party_name,
        birth_date=birth[0] if birth else None,
        birth_date_precision=birth[1] if birth else None,
        birth_date_source_url=url if birth else None,
        career_summary=career_summary,
        career_source_url=url if career_summary else None,
        profile_source_url=url,
        profile_source_type="party_official",
        profile_source_checked_at=date.today().isoformat(),
    )


def parse_craj_profile(url: str, body: bytes, member: dict[str, str]) -> PartyProfileEnrichment | None:
    doc = html.fromstring(body)
    full_text = clean_text(doc.text_content())
    if not page_contains_name(full_text, member["name_kanji"], member.get("name_kana")):
        return None

    table_values: dict[str, str] = {}
    for row in doc.xpath('//tr[.//th and .//td]'):
        th = clean_text(" ".join(row.xpath("./th//text()")))
        td = clean_text(" ".join(row.xpath("./td//text()")))
        if th and td:
            table_values[th] = td

    birth = parse_birth_date(table_values.get("生年月日", ""), allow_unlabeled=True)
    career_parts: list[str] = []
    label_map = {
        "役職": "役職",
        "国会の所属委員会 ／役職": "国会の所属委員会／役職",
        "経歴等": "経歴等",
        "学歴": "学歴",
    }
    for source_label, display_label in label_map.items():
        value = table_values.get(source_label)
        if value:
            career_parts.append(f"{display_label}: {value}")
    career_summary = clean_text(" / ".join(career_parts)) or None
    if not birth and not career_summary:
        return None

    return PartyProfileEnrichment(
        name_kanji=member["name_kanji"],
        name_kana=member["name_kana"],
        house="shugiin",
        party_name="中道改革連合",
        birth_date=birth[0] if birth else None,
        birth_date_precision=birth[1] if birth else None,
        birth_date_source_url=url if birth else None,
        career_summary=career_summary,
        career_source_url=url if career_summary else None,
        profile_source_url=url,
        profile_source_type="party_official",
        profile_source_checked_at=date.today().isoformat(),
    )


def labeled_birth_date(lines: list[str]) -> tuple[str, str] | None:
    for index, line in enumerate(lines):
        if line == "生年月日" or line.startswith("生年月日 "):
            candidates = [line.removeprefix("生年月日").strip(), *lines[index + 1 : index + 4]]
            for candidate in candidates:
                parsed = parse_birth_date(candidate, allow_unlabeled=True)
                if parsed:
                    return parsed
    return None


def candidate_queries(member: dict[str, str]) -> list[tuple[str, list[str]]]:
    name = member["name_kanji"].replace(" ", "")
    party_name = canonical_party_name(member["party_name"])
    domains = PARTY_DOMAINS.get(party_name, [])
    queries: list[tuple[str, list[str]]] = []
    for domain in domains:
        queries.append((f"site:{domain} {name} 衆議院議員 生年月日 経歴", [domain]))
        queries.append((f"site:{domain} {name} 議員 プロフィール", [domain]))
    return queries


def find_enrichment(member: dict[str, str], *, search_fallback: bool = True) -> tuple[PartyProfileEnrichment | None, list[str]]:
    if member["party_name"] == "自由民主党":
        url = jimin_profile_url(member)
        if url:
            try:
                parsed = parse_party_profile(url, fetch(url), member, "自由民主党")
            except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as exc:
                return None, [f"{url} ({exc})"]
            if parsed:
                return parsed, [url]
            return None, [url]
        if not search_fallback:
            return None, []

    direct = direct_party_enrichment(member)
    if direct:
        return direct, [direct.profile_source_url]
    if not search_fallback:
        return None, []

    checked: list[str] = []
    if not search_fallback:
        return None, checked
    for query, allowed_domains in candidate_queries(member):
        for url in search_urls(query):
            if url in checked:
                continue
            checked.append(url)
            if not is_official_party_url(url, allowed_domains):
                continue
            try:
                parsed = parse_party_profile(url, fetch(url), member, PARTY_DOMAIN_TO_NAME.get(domain_of(url), member["party_name"]))
            except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as exc:
                print(f"warn: fetch failed {url}: {exc}")
                continue
            if parsed:
                return parsed, checked
            time.sleep(0.2)
        time.sleep(1.0)
    return None, checked


def direct_party_enrichment(member: dict[str, str]) -> PartyProfileEnrichment | None:
    party = canonical_party_name(member["party_name"])
    if party == "日本維新の会":
        return page_enrichment_from_urls(member, ishin_profile_urls(), "日本維新の会")
    if party == "国民民主党":
        return page_enrichment_from_urls(member, kokumin_profile_urls(), "国民民主党")
    if party == "参政党":
        return sanseito_enrichment(member)
    if party == "日本共産党":
        return jcp_enrichment(member)
    if party == "中道改革連合・無所属":
        return page_enrichment_from_urls(member, craj_profile_urls(), "中道改革連合")
    if party == "チームみらい":
        return page_enrichment_from_urls(member, team_mirai_profile_urls(), "チームみらい")
    return None


def page_enrichment_from_urls(member: dict[str, str], urls: list[str], party_name: str) -> PartyProfileEnrichment | None:
    for url in urls:
        try:
            body = fetch(url)
            parsed = parse_craj_profile(url, body, member) if party_name == "中道改革連合" else parse_party_profile(url, body, member, party_name)
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError):
            continue
        if parsed:
            return parsed
    return None


_ISHIN_PROFILE_URLS: list[str] | None = None


def ishin_profile_urls() -> list[str]:
    global _ISHIN_PROFILE_URLS
    if _ISHIN_PROFILE_URLS is None:
        doc = html.fromstring(fetch(ISHIN_SHUGIIN_URL))
        urls: list[str] = []
        for href in doc.xpath('//a[contains(@href, "/member/detail/")]/@href'):
            url = urljoin(ISHIN_SHUGIIN_URL, href)
            if url not in urls:
                urls.append(url)
        _ISHIN_PROFILE_URLS = urls
    return _ISHIN_PROFILE_URLS


_KOKUMIN_PROFILE_URLS: dict[str, str] | None = None


def kokumin_profile_urls() -> list[str]:
    return list(load_kokumin_profile_url_map().values())


def load_kokumin_profile_url_map() -> dict[str, str]:
    global _KOKUMIN_PROFILE_URLS
    if _KOKUMIN_PROFILE_URLS is None:
        doc = html.fromstring(fetch(KOKUMIN_MEMBER_URL))
        mapping: dict[str, str] = {}
        for a in doc.xpath('//a[@href]'):
            name = clean_text(a.text_content())
            href = a.get("href")
            if not name or not href or "/member/" not in href:
                continue
            mapping[normalize_name(name)] = urljoin(KOKUMIN_MEMBER_URL, href)
        _KOKUMIN_PROFILE_URLS = mapping
    return _KOKUMIN_PROFILE_URLS


_CRAJ_PROFILE_URLS: list[str] | None = None


def craj_profile_urls() -> list[str]:
    global _CRAJ_PROFILE_URLS
    if _CRAJ_PROFILE_URLS is None:
        doc = html.fromstring(fetch(CRAJ_MEMBERS_URL))
        urls: list[str] = []
        for href in doc.xpath('//a[contains(@href, "/member/")]/@href'):
            url = urljoin(CRAJ_MEMBERS_URL, href)
            if url not in urls:
                urls.append(url)
        _CRAJ_PROFILE_URLS = urls
    return _CRAJ_PROFILE_URLS


_TEAM_MIRAI_PROFILE_URLS: list[str] | None = None


def team_mirai_profile_urls() -> list[str]:
    global _TEAM_MIRAI_PROFILE_URLS
    if _TEAM_MIRAI_PROFILE_URLS is None:
        doc = html.fromstring(fetch(TEAM_MIRAI_SHUGIIN_URL))
        urls: list[str] = []
        for href in doc.xpath('//a[contains(@href, "/election/shugiin-2026/members/")]/@href'):
            url = urljoin(TEAM_MIRAI_SHUGIIN_URL, href)
            if url not in urls:
                urls.append(url)
        _TEAM_MIRAI_PROFILE_URLS = urls
    return _TEAM_MIRAI_PROFILE_URLS


def sanseito_enrichment(member: dict[str, str]) -> PartyProfileEnrichment | None:
    target = normalize_name(member["name_kanji"])
    for row in load_sanseito_rows():
        if "衆議院" not in str(row.get("所属議会", "")) and row.get("選挙区分") != "衆議院議員":
            continue
        if normalize_name(str(row.get("名前大", ""))) != target:
            continue
        summary = clean_text(re.sub(r"<[^>]+>", " ", str(row.get("プロフィール") or row.get("略歴") or "")))
        birth = parse_birth_date(summary)
        if not summary:
            return None
        return PartyProfileEnrichment(
            name_kanji=member["name_kanji"],
            name_kana=member["name_kana"],
            house="shugiin",
            party_name="参政党",
            birth_date=birth[0] if birth else None,
            birth_date_precision=birth[1] if birth else None,
            birth_date_source_url=SANSEITO_CANDIDATE_JSON if birth else None,
            career_summary=summary,
            career_source_url=SANSEITO_MEMBER_JSON,
            profile_source_url=SANSEITO_MEMBER_JSON,
            profile_source_type="party_official",
            profile_source_checked_at=date.today().isoformat(),
        )
    return None


_SANSEITO_ROWS: list[dict[str, object]] | None = None


def load_sanseito_rows() -> list[dict[str, object]]:
    global _SANSEITO_ROWS
    if _SANSEITO_ROWS is None:
        rows = json.loads(fetch(SANSEITO_MEMBER_JSON).decode("utf-8"))
        candidates = json.loads(fetch(SANSEITO_CANDIDATE_JSON).decode("utf-8")).get("candidate_posts", [])
        _SANSEITO_ROWS = [*rows, *candidates]
    return _SANSEITO_ROWS


def jcp_enrichment(member: dict[str, str]) -> PartyProfileEnrichment | None:
    blocks = jcp_member_blocks()
    block = blocks.get(normalize_name(member["name_kanji"]))
    if not block:
        return None
    summary = career_from_lines(block)
    if not summary:
        return None
    return PartyProfileEnrichment(
        name_kanji=member["name_kanji"],
        name_kana=member["name_kana"],
        house="shugiin",
        party_name="日本共産党",
        birth_date=None,
        birth_date_precision=None,
        birth_date_source_url=None,
        career_summary=summary,
        career_source_url=JCP_SHUGIIN_URL,
        profile_source_url=JCP_SHUGIIN_URL,
        profile_source_type="party_official",
        profile_source_checked_at=date.today().isoformat(),
    )


_JCP_BLOCKS: dict[str, list[str]] | None = None


def jcp_member_blocks() -> dict[str, list[str]]:
    global _JCP_BLOCKS
    if _JCP_BLOCKS is not None:
        return _JCP_BLOCKS
    doc = html.fromstring(fetch(JCP_SHUGIIN_URL))
    lines = [clean_text(line) for line in doc.text_content().splitlines()]
    lines = [line for line in lines if line]
    blocks: dict[str, list[str]] = {}
    current_name: str | None = None
    current_lines: list[str] = []
    for line in lines:
        if line in {"塩川鉄也", "辰巳孝太郎", "田村智子", "畑野君枝"}:
            if current_name:
                blocks[current_name] = current_lines
            current_name = normalize_name(line)
            current_lines = [line]
        elif current_name:
            current_lines.append(line)
    if current_name:
        blocks[current_name] = current_lines
    _JCP_BLOCKS = blocks
    return blocks


def jimin_profile_url(member: dict[str, str]) -> str | None:
    rows = load_jimin_member_rows()
    target_name = normalize_name(member["name_kanji"])
    target_kana = normalize_name(member["name_kana"])
    for row in rows:
        if row.get("parliament") != "衆議院議員":
            continue
        name = normalize_name(f"{row.get('lastName', '')}{row.get('firstName', '')}")
        kana = normalize_name(f"{row.get('lastNameKana', '')}{row.get('firstNameKana', '')}")
        if name == target_name or (target_kana and kana == target_kana):
            return urljoin("https://www.jimin.jp", row["url"])
    return None


_JIMIN_MEMBER_ROWS: list[dict[str, str]] | None = None


def load_jimin_member_rows() -> list[dict[str, str]]:
    global _JIMIN_MEMBER_ROWS
    if _JIMIN_MEMBER_ROWS is None:
        _JIMIN_MEMBER_ROWS = json.loads(fetch(JIMIN_MEMBER_JSON).decode("utf-8"))
    return _JIMIN_MEMBER_ROWS


def build_sql(rows: list[PartyProfileEnrichment]) -> str:
    values = ",\n".join(
        "("
        + ", ".join(
            [
                sql_literal(row.name_kanji),
                sql_literal(row.name_kana),
                sql_literal(row.birth_date),
                sql_literal(row.birth_date_precision),
                sql_literal(row.birth_date_source_url),
                sql_literal(row.career_summary),
                sql_literal(row.career_source_url),
                sql_literal(row.profile_source_url),
                sql_literal(row.profile_source_type),
                sql_literal(row.profile_source_checked_at),
            ]
        )
        + ")"
        for row in rows
    )
    return f"""-- Generated at {datetime.now(timezone.utc).isoformat()}
-- Sources: party official profile pages discovered from search results.

update public.legislators as l
set
  birth_date = coalesce(v.birth_date::date, l.birth_date),
  birth_date_precision = coalesce(v.birth_date_precision, l.birth_date_precision),
  birth_date_source_url = coalesce(v.birth_date_source_url, l.birth_date_source_url),
  career_summary = coalesce(v.career_summary, l.career_summary),
  career_source_url = coalesce(v.career_source_url, l.career_source_url),
  profile_source_url = v.profile_source_url,
  profile_source_type = v.profile_source_type,
  profile_source_checked_at = v.profile_source_checked_at::date,
  scraped_at = now(),
  updated_at = now()
from (
  values
{values}
) as v(
  name_kanji,
  name_kana,
  birth_date,
  birth_date_precision,
  birth_date_source_url,
  career_summary,
  career_source_url,
  profile_source_url,
  profile_source_type,
  profile_source_checked_at
)
where l.house = 'shugiin'
  and l.name_kanji = v.name_kanji
  and l.name_kana = v.name_kana;
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--party", action="append", help="Limit to one or more party names")
    parser.add_argument("--no-search", action="store_true", help="Skip search fallback and use direct official indexes only")
    args = parser.parse_args()

    members = json.loads(SHUGIIN_MEMBERS_PATH.read_text(encoding="utf-8"))
    if args.party:
        allowed_parties = {canonical_party_name(party) for party in args.party}
        members = [member for member in members if canonical_party_name(member["party_name"]) in allowed_parties]
    enrichments: list[PartyProfileEnrichment] = []
    unresolved: list[dict[str, object]] = []

    for index, member in enumerate(members, start=1):
        if canonical_party_name(member["party_name"]) not in PARTY_DOMAINS:
            unresolved.append({**member, "reason": "no_party_domain_mapping"})
            continue
        enrichment, checked = find_enrichment(member, search_fallback=not args.no_search)
        if enrichment:
            enrichments.append(enrichment)
            print(f"[{index}/{len(members)}] ok {member['name_kanji']} {enrichment.profile_source_url}", flush=True)
        else:
            unresolved.append({**member, "reason": "party_profile_not_found", "checked_urls": checked[:10]})
            print(f"[{index}/{len(members)}] missing {member['name_kanji']}", flush=True)

    OUT_JSON.write_text(json.dumps([asdict(row) for row in enrichments], ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_UNRESOLVED.write_text(json.dumps(unresolved, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_SQL.write_text(build_sql(enrichments) if enrichments else "", encoding="utf-8")

    print(f"enriched={len(enrichments)}")
    print(f"with_birth_date={sum(1 for row in enrichments if row.birth_date)}")
    print(f"with_career_summary={sum(1 for row in enrichments if row.career_summary)}")
    print(f"unresolved={len(unresolved)}")
    print(f"json={OUT_JSON}")
    print(f"unresolved_json={OUT_UNRESOLVED}")
    print(f"sql={OUT_SQL}")


if __name__ == "__main__":
    main()
