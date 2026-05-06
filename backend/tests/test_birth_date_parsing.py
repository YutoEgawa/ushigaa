import unittest

from scripts.enrich_legislator_profiles import parse_birth_date


class BirthDateParsingTest(unittest.TestCase):
    def test_ignores_current_as_of_date_and_uses_birth_sentence(self):
        text = "令和8年5月5日現在 １９６７年７月１１日生。長崎大医学部卒"
        self.assertEqual(parse_birth_date(text), ("1967-07-11", "day"))

    def test_ignores_unlabeled_career_dates(self):
        text = "2007年4月から地域活動を開始。2023年4月に立候補。"
        self.assertIsNone(parse_birth_date(text))

    def test_uses_birth_marker_with_western_year(self):
        text = "1997年生まれ、北海道出身。北海道教育大学札幌校を卒業。"
        self.assertEqual(parse_birth_date(text), ("1997-01-01", "year"))

    def test_labeled_values_can_be_unlabeled_dates(self):
        self.assertEqual(parse_birth_date("1998年11月26日", allow_unlabeled=True), ("1998-11-26", "day"))

    def test_rejects_impossibly_young_birth_date(self):
        self.assertIsNone(parse_birth_date("2023年4月生まれ"))


if __name__ == "__main__":
    unittest.main()
