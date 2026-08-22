#!/usr/bin/env python3
"""Standard-library tests for conservative L3 split-name candidate recall."""
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import match_mqww_cbdb_l3 as l3


class TestSplitNameRecall(unittest.TestCase):
    def test_split_boundaries_include_single_and_compound_surname(self):
        self.assertEqual(l3.split_name("李清照"), [("李", "清照"), ("李清", "照")])
        self.assertEqual(l3.split_name("歐陽修"), [("歐", "陽修"), ("歐陽", "修")])

    def test_blank_and_too_short_have_no_split(self):
        self.assertEqual(l3.split_name(""), [])
        self.assertEqual(l3.split_name("氏"), [])

    def test_variant_characters_are_not_silently_folded(self):
        index = {("臺", "靜農"): [("1", "臺靜農", False)]}
        self.assertEqual(l3.recall_candidates("台靜農", index), [])

    def test_generic_names_are_excluded(self):
        rows = l3.match_l3(
            [{"poetID": "p1", "NameHZ": "王氏"}],
            {"p1": {"level": "C", "candidate_personids": ""}}, {},
            {("王", "氏"): [("1", "王氏", True)]},
        )
        self.assertEqual(rows[0]["status"], "skip_l0")
        self.assertEqual(rows[0]["n_candidates"], "0")

    def test_multiple_candidates_stay_pending(self):
        index = {("李", "清照"): [("10", "李清炤", True), ("20", "李清照", True)]}
        rows = l3.match_l3(
            [{"poetID": "p1", "NameHZ": "李清照"}],
            {"p1": {"level": "D", "candidate_personids": ""}},
            {"p1": {"status": "no_alias_match", "candidate_personids": ""}}, index,
        )
        row = rows[0]
        self.assertEqual(row["match_method"], "l3_split_name")
        self.assertEqual(row["candidate_source"], "BIOG_MAIN.c_surname_chn+c_mingzi_chn")
        self.assertEqual(row["rule_version"], l3.RULE_VERSION)
        self.assertEqual(row["reviewer_decision"], "pending_human_review")
        self.assertEqual(row["status"], "pending_human_review")
        self.assertEqual(row["candidate_personids"], "10|20")
        self.assertEqual(row["n_candidates"], "2")
        self.assertEqual(row["level_l1"], "D")

    def test_l1_and_l2_matches_are_not_promoted_or_reissued(self):
        index = {("李", "清照"): [("10", "李清照", True)]}
        poets = [{"poetID": "p1", "NameHZ": "李清照"}, {"poetID": "p2", "NameHZ": "李清照"}]
        baseline = {
            "p1": {"level": "A", "candidate_personids": "10"},
            "p2": {"level": "D", "candidate_personids": ""},
        }
        l2_rows = {
            "p1": {"status": "existing_l1_match", "candidate_personids": ""},
            "p2": {"status": "review_unique_female", "candidate_personids": "10"},
        }
        rows = l3.match_l3(poets, baseline, l2_rows, index)
        self.assertEqual(rows[0]["status"], "existing_l1_match")
        self.assertEqual(rows[1]["status"], "existing_l2_candidate")
        self.assertEqual(rows[0]["candidate_personids"], "")
        self.assertEqual(rows[1]["candidate_personids"], "")


class TestIndexAndManifest(unittest.TestCase):
    def test_component_index_strips_fields_and_preserves_variants(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "x.db"
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE BIOG_MAIN (c_personid INTEGER,c_name_chn TEXT,c_surname_chn TEXT,c_mingzi_chn TEXT,c_female INTEGER)")
            conn.executemany("INSERT INTO BIOG_MAIN VALUES (?,?,?,?,?)", [
                (1, "別寫", " 李 ", " 清照 ", 1), (2, "空", "", "清照", 1),
            ])
            conn.commit()
            idx = l3.load_split_index(conn, {("李", "清照")})
            self.assertEqual(idx, {("李", "清照"): [("1", "別寫", True)]})

    def test_manifest_counts_new_overlap_and_conflict(self):
        rows = [
            {"poetID": "p1", "status": "pending_human_review", "candidate_personids": "1|2",
             "prior_candidate_personids": "1"},
            {"poetID": "p2", "status": "pending_human_review", "candidate_personids": "3",
             "prior_candidate_personids": "4"},
            {"poetID": "p3", "status": "no_split_match", "candidate_personids": "",
             "prior_candidate_personids": ""},
        ]
        stats = l3.summarize(rows)
        self.assertEqual(stats["new_candidate_pairs"], 2)
        self.assertEqual(stats["overlap_candidate_pairs"], 1)
        self.assertEqual(stats["conflict_records"], 1)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "manifest.json"
            l3.write_manifest(path, stats, "db", "mqww", "l1", "l2", "out")
            manifest = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], "mqww_cbdb_l3_manifest_v1")
            self.assertEqual(manifest["review_policy"], "pending_human_review_only")
            self.assertFalse(manifest["creates_relationship_edges"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
