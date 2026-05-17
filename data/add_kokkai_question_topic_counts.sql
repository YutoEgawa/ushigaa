-- Adds an aggregate view for ranking legislators by question volume per meeting topic since 2023.

create or replace view public.kokkai_question_topic_counts
with (security_invoker = true)
as
select
  g.legislator_id,
  coalesce(nullif(m.meeting_topic, ''), '調査会') as meeting_topic,
  count(*)::integer as question_count
from public.kokkai_question_groups g
join public.kokkai_meetings m on m.id = g.meeting_id
where m.date >= date '2023-01-01'
group by g.legislator_id, coalesce(nullif(m.meeting_topic, ''), '調査会');

grant select on public.kokkai_question_topic_counts to anon, authenticated;
