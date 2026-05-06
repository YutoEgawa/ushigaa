# API Contract

Base path: `/v1`

## `GET /health`

Returns API health.

## `GET /legislators`

Query parameters:

- `house`: `shugiin` or `sangiin`
- `party`: exact party name
- `district`: exact district name
- `q`: text search across name, kana, party, and district
- `limit`: 1-100, default 50
- `offset`: default 0

Returns:

```json
{
  "items": [
    {
      "id": "uuid",
      "name_kanji": "赤松 健",
      "name_kana": "あかまつ けん",
      "house": "sangiin",
      "party_name": "自由民主党",
      "district_name": "比例",
      "election_count": 1,
      "birth_date": "1968-07-05",
      "birth_date_precision": "day",
      "career_summary": "公式プロフィール由来の略歴",
      "profile_source_url": "https://...",
      "profile_source_type": "diet_official",
      "profile_source_checked_at": "2026-05-05"
    }
  ],
  "limit": 50,
  "offset": 0,
  "count": 712
}
```

## `GET /legislators/{id}`

Returns one active legislator or `404`.

Legislator records include profile enrichment fields when available:

- `birth_date`: parsed birth date. If only month/year is known, this stores the first day/month as a placeholder.
- `birth_date_precision`: `day`, `month`, `year`, or `unknown`
- `birth_date_source_url`: source URL for birth date
- `election_count`: current chamber election count when available
- `election_count_note`: raw count note, including cross-chamber notes
- `election_count_source_url`: source URL for election count
- `career_summary`: source-backed profile/career summary
- `career_source_url`: source URL for career summary
- `profile_source_url`: primary profile source URL
- `profile_source_type`: `diet_official`, `party_official`, `personal_official`, or `other`
- `profile_source_checked_at`: source check date

## `GET /parties`

Returns party master records.

Query parameters:

- `house`: optional `shugiin` or `sangiin`

Party records include power-map alignment fields:

- `alignment`: `ruling`, `opposition`, or `other`
- `alignment_rank`: display rank within the same alignment group
- `alignment_rank_member_count`: active legislator count used to derive the rank
- `alignment_basis`: source/ranking rule note
- `alignment_source_url`: external source URL for the ruling/opposition classification
- `alignment_source_checked_at`: source check date

When `house` is provided, `alignment_rank` and `alignment_rank_member_count` are derived from active legislator counts inside that house only. The response includes only parties with active members in the requested house.

When `house` is omitted, the endpoint returns party master records with the stored aggregate alignment fields.

## `GET /districts`

Query parameters:

- `house`: optional `shugiin` or `sangiin`

Returns district master records.

## `POST /contact`

Sends a contact form submission to the ウシガー operator email address.

Request:

```json
{
  "name": "山田 太郎",
  "organization": "任意の所属",
  "email": "taro@example.com",
  "type": "wrong-info",
  "detail": "問い合わせ本文"
}
```

`type` accepts:

- `wrong-info`: 誤った情報のご指摘
- `improvement`: 改善のご要望
- `other`: その他、運営へのお問い合わせ

Response:

```json
{ "status": "sent" }
```

Required SendGrid settings for mail delivery:

- `SENDGRID_API_KEY`
- `SENDGRID_FROM_EMAIL`, must be a SendGrid authenticated sender
- `SENDGRID_FROM_NAME`, default `ウシガー`
- `CONTACT_RECIPIENT_EMAIL`, default `y.egawa.ahstu0415@gmail.com`
