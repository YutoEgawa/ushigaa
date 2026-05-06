-- Corrects implausible birth dates caused by scraping update dates or career dates.
-- Applied to Supabase on 2026-05-06.

with corrected(name_kanji, name_kana, house, birth_date, birth_date_precision) as (
  values
    ('秋野 公造','あきの こうぞう','sangiin','1967-07-11'::date,'day'),
    ('浅田 均','あさだ ひとし','sangiin','1950-01-01'::date,'year'),
    ('石垣 のりこ','いしがき のりこ','sangiin','1974-01-01'::date,'year'),
    ('伊勢崎 賢治','いせざき けんじ','sangiin','1957-07-06'::date,'day'),
    ('猪口 邦子','いのぐち くにこ','sangiin','1952-01-01'::date,'year'),
    ('かごしま 彰宏','かごしま あきひろ','sangiin','1988-12-08'::date,'day'),
    ('川 裕一郎','かわ ゆういちろう','shugiin','1971-01-01'::date,'year'),
    ('郡山 りょう','こおりやま りょう','sangiin','1974-01-01'::date,'year'),
    ('古賀 友一郎','こが ゆういちろう','sangiin','1967-11-02'::date,'day'),
    ('櫻井 充','さくらい みつる','sangiin','1956-01-01'::date,'year'),
    ('竹谷 とし子','たけや としこ','sangiin','1969-01-01'::date,'year'),
    ('仁比 聡平','にひ そうへい','sangiin','1963-10-16'::date,'day'),
    ('平山 佐知子','ひらやま さちこ','sangiin','1971-01-01'::date,'year'),
    ('松川 るい','まつかわ るい','sangiin','1971-01-01'::date,'year'),
    ('松田 学','まつだ まなぶ','sangiin','1957-11-11'::date,'day'),
    ('松村 祥史','まつむら よしふみ','sangiin','1964-04-22'::date,'day'),
    ('山田 太郎','やまだ たろう','sangiin','1967-05-12'::date,'day'),
    ('ラサール石井','らさーるいしい','sangiin','1955-01-01'::date,'year'),
    ('渡辺 猛之','わたなべ たけゆき','sangiin','1968-04-18'::date,'day')
)
update public.legislators l
set birth_date = c.birth_date,
    birth_date_precision = c.birth_date_precision,
    updated_at = now()
from corrected c
where l.name_kanji = c.name_kanji
  and l.name_kana = c.name_kana
  and l.house = c.house;

update public.legislators
set birth_date = null,
    birth_date_precision = null,
    birth_date_source_url = null,
    updated_at = now()
where (name_kanji, name_kana, house) in (
  ('宇佐美 登','うさみ のぼる','shugiin'),
  ('江原 くみ子','えはら くみこ','sangiin'),
  ('片山 さつき','かたやま さつき','sangiin'),
  ('木村 義雄','きむら よしお','sangiin'),
  ('鈴木 大地','すずき だいち','sangiin'),
  ('鈴木 美香','すずき みか','shugiin'),
  ('高鳥 修一','たかとり しゅういち','shugiin'),
  ('寺田 静','てらた しずか','sangiin'),
  ('浜田 靖一','はまだ やすかず','shugiin'),
  ('森 まさこ','もり まさこ','sangiin')
);
