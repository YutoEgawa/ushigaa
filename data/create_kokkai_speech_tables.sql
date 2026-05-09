-- Stores only question-candidate Diet speeches for Ushigaa.
-- Source IDs from kokkai.ndl.go.jp are kept separate from Supabase UUIDs.

create table if not exists public.kokkai_meetings (
  id uuid primary key default extensions.uuid_generate_v4(),
  source_issue_id text not null unique,
  name_of_house text,
  name_of_meeting text not null,
  date date not null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

comment on table public.kokkai_meetings is '国会APIの会議録メタデータ。source_issue_id は国会API上の issueID。';

create table if not exists public.kokkai_speeches (
  id uuid primary key default extensions.uuid_generate_v4(),
  legislator_id uuid not null references public.legislators(id) on delete cascade,
  meeting_id uuid not null references public.kokkai_meetings(id) on delete cascade,
  source_speech_id text not null unique,
  source_issue_id text not null,
  speech_order integer,
  speaker text not null,
  speaker_position text,
  speech text not null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

comment on table public.kokkai_speeches is '国会APIの発言。Ushigaaでは本人一致かつ speakerPosition is null の質問候補のみ保存する。';
comment on column public.kokkai_speeches.legislator_id is 'Ushigaa/Supabase側の議員UUID。国会API IDとは別。';
comment on column public.kokkai_speeches.source_speech_id is '国会API上の speechID。';
comment on column public.kokkai_speeches.source_issue_id is '国会API上の issueID。';

create index if not exists kokkai_meetings_date_idx
  on public.kokkai_meetings (date desc);

create index if not exists kokkai_speeches_legislator_idx
  on public.kokkai_speeches (legislator_id);

create index if not exists kokkai_speeches_legislator_meeting_idx
  on public.kokkai_speeches (legislator_id, meeting_id);

create index if not exists kokkai_speeches_issue_order_idx
  on public.kokkai_speeches (source_issue_id, speech_order);

create table if not exists public.kokkai_question_groups (
  id uuid primary key default extensions.uuid_generate_v4(),
  legislator_id uuid not null references public.legislators(id) on delete cascade,
  meeting_id uuid not null references public.kokkai_meetings(id) on delete cascade,
  speaker text not null,
  speech_count integer not null,
  speech text not null,
  source_issue_ids text[] not null default '{}',
  source_speech_ids text[] not null default '{}',
  first_speech_order integer,
  last_speech_order integer,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  unique (legislator_id, meeting_id, speaker)
);

comment on table public.kokkai_question_groups is 'Ushigaaの表示・分析単位。発言を date + meeting + speaker でまとめた質疑グループ。';
comment on column public.kokkai_question_groups.speech is '同一会議日の対象発言を speech_order 順に結合した本文。';

create index if not exists kokkai_question_groups_legislator_idx
  on public.kokkai_question_groups (legislator_id);

create index if not exists kokkai_question_groups_meeting_idx
  on public.kokkai_question_groups (meeting_id);

create or replace view public.kokkai_question_speech_rows
with (security_invoker = true)
as
select
  s.legislator_id,
  m.date,
  m.name_of_house,
  m.name_of_meeting,
  s.speaker,
  s.speech,
  s.source_speech_id,
  s.source_issue_id,
  s.speech_order
from public.kokkai_speeches s
join public.kokkai_meetings m on m.id = s.meeting_id
where s.speaker_position is null;

create or replace view public.kokkai_question_group_rows
with (security_invoker = true)
as
select
  g.id,
  g.legislator_id,
  m.date,
  m.name_of_house,
  m.name_of_meeting,
  g.speaker,
  g.speech_count,
  g.speech,
  g.source_issue_ids,
  g.source_speech_ids,
  g.first_speech_order,
  g.last_speech_order
from public.kokkai_question_groups g
join public.kokkai_meetings m on m.id = g.meeting_id;

alter table public.kokkai_meetings enable row level security;
alter table public.kokkai_speeches enable row level security;
alter table public.kokkai_question_groups enable row level security;

drop policy if exists "Public read kokkai meetings" on public.kokkai_meetings;
create policy "Public read kokkai meetings"
  on public.kokkai_meetings
  for select
  using (true);

drop policy if exists "Public read kokkai speeches" on public.kokkai_speeches;
create policy "Public read kokkai speeches"
  on public.kokkai_speeches
  for select
  using (true);

drop policy if exists "Public read kokkai question groups" on public.kokkai_question_groups;
create policy "Public read kokkai question groups"
  on public.kokkai_question_groups
  for select
  using (true);

grant select on public.kokkai_meetings to anon, authenticated;
grant select on public.kokkai_speeches to anon, authenticated;
grant select on public.kokkai_question_groups to anon, authenticated;
grant select on public.kokkai_question_speech_rows to anon, authenticated;
grant select on public.kokkai_question_group_rows to anon, authenticated;
