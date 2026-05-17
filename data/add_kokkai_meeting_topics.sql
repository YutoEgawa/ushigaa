-- Adds a broad topic label derived from kokkai_meetings.name_of_meeting.

alter table public.kokkai_meetings
  add column if not exists meeting_topic text;

comment on column public.kokkai_meetings.meeting_topic is
  'name_of_meeting から推定した会議・委員会の大分類トピック。';

update public.kokkai_meetings
set meeting_topic = case
  when name_of_meeting like '%本会議%' then '本会議'
  when name_of_meeting like '%議院運営%' then '議院運営'
  when name_of_meeting like '%予算委員会%' then '予算'
  when name_of_meeting like '%決算%' or name_of_meeting like '%行政監視%' then '決算・行政監視'
  when name_of_meeting like '%財務金融%' or name_of_meeting like '%財政金融%' then '財政・金融'
  when name_of_meeting like '%外交%' or name_of_meeting like '%外務%' or name_of_meeting like '%安全保障%' or name_of_meeting like '%防衛%' or name_of_meeting like '%国際%' or name_of_meeting like '%政府開発援助%' then '外交・安全保障'
  when name_of_meeting like '%厚生労働%' then '厚生労働'
  when name_of_meeting like '%こども%' or name_of_meeting like '%子育て%' or name_of_meeting like '%若者%' then 'こども・子育て'
  when name_of_meeting like '%法務%' then '法務'
  when name_of_meeting like '%文教%' or name_of_meeting like '%文部科学%' then '教育・科学'
  when name_of_meeting like '%経済産業%' or name_of_meeting like '%資源エネルギー%' or name_of_meeting like '%原子力%' then '経済産業・エネルギー'
  when name_of_meeting like '%環境%' or name_of_meeting like '%持続可能%' then '環境'
  when name_of_meeting like '%農林水産%' then '農林水産'
  when name_of_meeting like '%国土交通%' then '国土交通'
  when name_of_meeting like '%総務%' then '総務・地方行政'
  when name_of_meeting like '%地方創生%' or name_of_meeting like '%地域活性化%' or name_of_meeting like '%デジタル%' or name_of_meeting like '%人工知能%' then '地方創生・デジタル'
  when name_of_meeting like '%消費者%' then '消費者'
  when name_of_meeting like '%内閣委員会%' or name_of_meeting like '%国家基本政策%' then '内閣・国家基本政策'
  when name_of_meeting like '%憲法%' then '憲法'
  when name_of_meeting like '%政治改革%' or name_of_meeting like '%政治倫理%' or name_of_meeting like '%公職選挙%' or name_of_meeting like '%選挙制度%' then '政治改革・選挙'
  when name_of_meeting like '%災害%' or name_of_meeting like '%復興%' then '災害・復興'
  when name_of_meeting like '%拉致%' or name_of_meeting like '%北朝鮮%' then '拉致・北朝鮮'
  when name_of_meeting like '%沖縄%' or name_of_meeting like '%北方%' then '沖縄・北方'
  when name_of_meeting like '%情報監視%' then '情報監視'
  when name_of_meeting like '%懲罰%' then '議員規律'
  when name_of_meeting like '%調査会%' then '調査会'
  else '調査会'
end
where meeting_topic is distinct from case
  when name_of_meeting like '%本会議%' then '本会議'
  when name_of_meeting like '%議院運営%' then '議院運営'
  when name_of_meeting like '%予算委員会%' then '予算'
  when name_of_meeting like '%決算%' or name_of_meeting like '%行政監視%' then '決算・行政監視'
  when name_of_meeting like '%財務金融%' or name_of_meeting like '%財政金融%' then '財政・金融'
  when name_of_meeting like '%外交%' or name_of_meeting like '%外務%' or name_of_meeting like '%安全保障%' or name_of_meeting like '%防衛%' or name_of_meeting like '%国際%' or name_of_meeting like '%政府開発援助%' then '外交・安全保障'
  when name_of_meeting like '%厚生労働%' then '厚生労働'
  when name_of_meeting like '%こども%' or name_of_meeting like '%子育て%' or name_of_meeting like '%若者%' then 'こども・子育て'
  when name_of_meeting like '%法務%' then '法務'
  when name_of_meeting like '%文教%' or name_of_meeting like '%文部科学%' then '教育・科学'
  when name_of_meeting like '%経済産業%' or name_of_meeting like '%資源エネルギー%' or name_of_meeting like '%原子力%' then '経済産業・エネルギー'
  when name_of_meeting like '%環境%' or name_of_meeting like '%持続可能%' then '環境'
  when name_of_meeting like '%農林水産%' then '農林水産'
  when name_of_meeting like '%国土交通%' then '国土交通'
  when name_of_meeting like '%総務%' then '総務・地方行政'
  when name_of_meeting like '%地方創生%' or name_of_meeting like '%地域活性化%' or name_of_meeting like '%デジタル%' or name_of_meeting like '%人工知能%' then '地方創生・デジタル'
  when name_of_meeting like '%消費者%' then '消費者'
  when name_of_meeting like '%内閣委員会%' or name_of_meeting like '%国家基本政策%' then '内閣・国家基本政策'
  when name_of_meeting like '%憲法%' then '憲法'
  when name_of_meeting like '%政治改革%' or name_of_meeting like '%政治倫理%' or name_of_meeting like '%公職選挙%' or name_of_meeting like '%選挙制度%' then '政治改革・選挙'
  when name_of_meeting like '%災害%' or name_of_meeting like '%復興%' then '災害・復興'
  when name_of_meeting like '%拉致%' or name_of_meeting like '%北朝鮮%' then '拉致・北朝鮮'
  when name_of_meeting like '%沖縄%' or name_of_meeting like '%北方%' then '沖縄・北方'
  when name_of_meeting like '%情報監視%' then '情報監視'
  when name_of_meeting like '%懲罰%' then '議員規律'
  when name_of_meeting like '%調査会%' then '調査会'
  else '調査会'
end;

create index if not exists kokkai_meetings_topic_idx
  on public.kokkai_meetings (meeting_topic);

create or replace view public.kokkai_question_speech_rows
with (security_invoker = true)
as
select
  s.legislator_id,
  m.date,
  m.name_of_house,
  m.name_of_meeting,
  m.meeting_topic,
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
  m.meeting_topic,
  g.speaker,
  g.speech_count,
  g.speech,
  g.source_issue_ids,
  g.source_speech_ids,
  g.first_speech_order,
  g.last_speech_order
from public.kokkai_question_groups g
join public.kokkai_meetings m on m.id = g.meeting_id;

grant select on public.kokkai_question_speech_rows to anon, authenticated;
grant select on public.kokkai_question_group_rows to anon, authenticated;
