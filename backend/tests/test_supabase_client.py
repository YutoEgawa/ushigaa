import unittest

from app.supabase_client import build_legislator_params, parse_content_range_count


class SupabaseClientTest(unittest.TestCase):
    def test_parse_content_range_count(self) -> None:
        self.assertEqual(parse_content_range_count("0-49/712"), 712)
        self.assertIsNone(parse_content_range_count("0-49/*"))
        self.assertIsNone(parse_content_range_count(None))

    def test_build_legislator_params_filters_and_search(self) -> None:
        params = build_legislator_params(
            house="shugiin",
            party="自由民主党",
            district="岡山1",
            q="逢沢",
            limit=20,
            offset=40,
        )

        self.assertTrue(str(params["select"]).startswith("id,name_kanji"))
        self.assertEqual(params["house"], "eq.shugiin")
        self.assertEqual(params["party_name"], "eq.自由民主党")
        self.assertEqual(params["district_name"], "eq.岡山1")
        self.assertEqual(params["limit"], 20)
        self.assertEqual(params["offset"], 40)
        self.assertIn("name_kanji.ilike.*逢沢*", str(params["or"]))


if __name__ == "__main__":
    unittest.main()
