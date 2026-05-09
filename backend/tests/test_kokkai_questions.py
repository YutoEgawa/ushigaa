from datetime import date
import unittest

from app.kokkai_questions import build_question_groups


class KokkaiQuestionGroupingTest(unittest.TestCase):
    def test_groups_same_date_meeting_and_speaker(self) -> None:
        rows = [
            {
                "date": "2025-11-20",
                "name_of_house": "参議院",
                "name_of_meeting": "文教科学委員会",
                "speaker": "赤松健",
                "speech": "質問一",
                "source_issue_id": "i1",
                "source_speech_id": "s1",
            },
            {
                "date": "2025-11-20",
                "name_of_house": "参議院",
                "name_of_meeting": "文教科学委員会",
                "speaker": "赤松健",
                "speech": "質問二",
                "source_issue_id": "i1",
                "source_speech_id": "s2",
            },
            {
                "date": "2025-11-28",
                "name_of_house": "参議院",
                "name_of_meeting": "こども・子育て・若者活躍に関する特別委員会",
                "speaker": "赤松健",
                "speech": "質問三",
                "source_issue_id": "i2",
                "source_speech_id": "s3",
            },
        ]

        questions = build_question_groups(rows)

        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0].date, date(2025, 11, 28))
        self.assertEqual(questions[1].speech_count, 2)
        self.assertEqual(questions[1].speech, "質問一\n\n質問二")
        self.assertEqual(questions[1].source_issue_ids, ["i1"])
        self.assertEqual(questions[1].source_speech_ids, ["s1", "s2"])


if __name__ == "__main__":
    unittest.main()
