import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from work_review import classify_gender, normalize_title_without_volumes, merge_decision


class WorkReviewTest(unittest.TestCase):
    def test_gender_keeps_unknown_distinct_without_name_guessing(self):
        self.assertEqual(classify_gender("1"), "female")
        self.assertEqual(classify_gender("0"), "male")
        self.assertEqual(classify_gender(""), "unknown")

    def test_title_normalization_removes_volume_only(self):
        self.assertEqual(
            normalize_title_without_volumes("冷紅軒詩集﹕二卷﹐附詞(清百保友蘭撰)"),
            "冷紅軒詩集﹐附詞(清百保友蘭撰)",
        )

    def test_only_volume_difference_is_merge_candidate(self):
        left = {"title_key": "書名(清某撰)", "worktype": "別集", "publisher": "甲", "place": "北京", "pub_statement": "清刻本", "volume": "一卷"}
        right = {**left, "volume": "二卷"}
        self.assertEqual(merge_decision(left, right), "candidate_merge_review")
        self.assertEqual(merge_decision(left, {**right, "publisher": "乙"}), "keep_separate")


if __name__ == "__main__":
    unittest.main()
