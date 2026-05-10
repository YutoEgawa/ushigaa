-- Stores official government role experience from the Prime Minister's Office / Cabinet Office sources.

create table if not exists public.legislator_government_roles (
  id uuid primary key default extensions.uuid_generate_v4(),
  legislator_id uuid references public.legislators(id) on delete set null,
  name_kanji text not null,
  normalized_name text not null,
  role_type text not null check (role_type in ('prime_minister', 'minister', 'senior_vice_minister', 'parliamentary_vice_minister')),
  role_title text not null,
  cabinet_name text not null,
  cabinet_started_on date,
  cabinet_ended_on date,
  source_name text not null,
  source_url text not null,
  source_checked_at date not null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  unique (normalized_name, role_type, role_title, cabinet_name, cabinet_started_on, source_url)
);

comment on table public.legislator_government_roles is '2023年1月以降の総理大臣・大臣・副大臣・大臣政務官経験。官邸/内閣府の一次情報をソースにする。';
comment on column public.legislator_government_roles.legislator_id is 'Ushigaa/Supabase側の議員UUID。現職議員に照合できない過去職者は null。';
comment on column public.legislator_government_roles.role_type is 'prime_minister, minister, senior_vice_minister, parliamentary_vice_minister の4分類。';

create index if not exists legislator_government_roles_legislator_idx
  on public.legislator_government_roles (legislator_id);

create index if not exists legislator_government_roles_normalized_name_idx
  on public.legislator_government_roles (normalized_name);

create index if not exists legislator_government_roles_role_type_idx
  on public.legislator_government_roles (role_type);

create or replace view public.legislator_government_role_flags
with (security_invoker = true)
as
select
  legislator_id,
  bool_or(role_type = 'prime_minister') as has_prime_minister_experience,
  bool_or(role_type = 'minister') as has_minister_experience,
  bool_or(role_type = 'senior_vice_minister') as has_senior_vice_minister_experience,
  bool_or(role_type = 'parliamentary_vice_minister') as has_parliamentary_vice_minister_experience,
  bool_or(role_type in ('prime_minister', 'minister', 'senior_vice_minister', 'parliamentary_vice_minister')) as has_executive_government_experience
from public.legislator_government_roles
where legislator_id is not null
group by legislator_id;

alter table public.legislator_government_roles enable row level security;

drop policy if exists "Public read legislator government roles" on public.legislator_government_roles;
create policy "Public read legislator government roles"
  on public.legislator_government_roles
  for select
  using (true);

grant select on public.legislator_government_roles to anon, authenticated;
grant select on public.legislator_government_role_flags to anon, authenticated;
