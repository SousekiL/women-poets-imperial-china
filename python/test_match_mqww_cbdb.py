#!/usr/bin/env python3
"""match_mqww_cbdb 单元与集成测试（仅标准库 unittest）。"""
from __future__ import annotations

import csv
import io
import os
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import match_mqww_cbdb as mm


class TestClassifyL0(unittest.TestCase):
    def test_generic_names(self):
        for name in ["王氏", "李氏", "無名氏", "佚名", "歐陽氏", "王張氏", "閨秀"]:
            self.assertTrue(mm.classify_l0(name), name)

    def test_real_names(self):
        for name in ["李清照", "沈英", "吳蕙", "王貞儀", "顧太清"]:
            self.assertFalse(mm.classify_l0(name), name)

    def test_blank(self):
        self.assertEqual(mm.classify_l0(""), "blank_name")
        self.assertEqual(mm.classify_l0("   "), "blank_name")


class TestMatch(unittest.TestCase):
    def setUp(self):
        self.index = {
            "李清照": [("1001", True)],
            "王貞儀": [("1002", True), ("2002", False)],   # 同名含女性 → B
            "沈英": [("1003", False)],                      # 非女性 → B
            "顧太清": [("1004", True)],
        }

    def _poets(self):
        return [
            {"poetID": "p1", "NameHZ": "李清照", "StartYear": "1084", "EndYear": "1155", "Sex": "F"},
            {"poetID": "p2", "NameHZ": "王氏", "StartYear": "", "EndYear": "", "Sex": "F"},
            {"poetID": "p3", "NameHZ": "王貞儀", "StartYear": "1768", "EndYear": "1797", "Sex": "F"},
            {"poetID": "p4", "NameHZ": "沈英", "StartYear": "", "EndYear": "", "Sex": "F"},
            {"poetID": "p5", "NameHZ": "查無此人", "StartYear": "", "EndYear": "", "Sex": "F"},
            {"poetID": "p6", "NameHZ": "顧太清", "StartYear": "1799", "EndYear": "1877", "Sex": "F"},
        ]

    def test_levels(self):
        rows = mm.match_poets(self._poets(), self.index)
        by_id = {r["poetID"]: r for r in rows}
        self.assertEqual(by_id["p1"]["level"], "A")      # 唯一女性候选
        self.assertEqual(by_id["p1"]["candidate_personids"], "1001")
        self.assertEqual(by_id["p2"]["level"], "C")      # L0 泛称
        self.assertEqual(by_id["p3"]["level"], "B")      # 多候选（含女性）
        self.assertEqual(by_id["p3"]["n_candidates"], "2")
        self.assertEqual(by_id["p3"]["n_female_candidates"], "1")
        self.assertEqual(by_id["p4"]["level"], "B")      # 命中但非女性
        self.assertEqual(by_id["p4"]["female_flagged"], "0")
        self.assertEqual(by_id["p5"]["level"], "D")      # 未命中
        self.assertEqual(by_id["p6"]["level"], "A")

    def test_summary_counts(self):
        rows = mm.match_poets(self._poets(), self.index)
        s = mm.summarize(rows, n_cbdb_total=6, n_cbdb_female=3)
        self.assertEqual(s["mqww_poet_records"], 6)
        self.assertEqual(s["matched"], 4)                # p1 p3 p4 p6
        self.assertEqual(s["female_flagged_matched"], 3)  # p1 p3 p6
        self.assertEqual(s["level_A"], 2)
        self.assertEqual(s["level_B"], 2)
        self.assertEqual(s["level_C"], 1)
        self.assertEqual(s["level_D"], 1)
        self.assertEqual(s["cbdb_female_rows"], 3)


class TestReadOnly(unittest.TestCase):
    def test_ro_uri_rejects_write(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "t.db"
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE t (x INTEGER)")
            con.execute("INSERT INTO t VALUES (1)")
            con.commit()
            con.close()
            ro = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            with self.assertRaises(sqlite3.OperationalError):
                ro.execute("INSERT INTO t VALUES (2)")


class TestEndToEnd(unittest.TestCase):
    def test_full_run(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            db = td / "cbdb_test.db"
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE BIOG_MAIN (c_personid INTEGER, c_name_chn CHAR(255), c_female BOOLEAN)")
            con.executemany(
                "INSERT INTO BIOG_MAIN VALUES (?,?,?)",
                [(1001, "李清照", 1), (1002, "沈英", 0), (1003, "王氏", 1)],
            )
            con.commit()
            con.close()

            poets = td / "poet.csv"
            poets.write_text(
                "poetID,NameHZ,StartYear,EndYear,Sex\n"
                "p1,李清照,1084,1155,F\n"
                "p2,王氏,,,F\n"
                "p3,沈英,,,F\n",
                encoding="utf-8",
            )
            out = td / "out.csv"
            summary = td / "summary.txt"
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mm.main(["--db", str(db), "--mqww-poet", str(poets),
                              "--out", str(out), "--summary-out", str(summary)])
            self.assertEqual(rc, 0)
            with open(out, encoding="utf-8-sig", newline="") as fh:
                rows = list(csv.DictReader(fh))
            by_id = {r["poetID"]: r for r in rows}
            self.assertEqual(by_id["p1"]["level"], "A")
            self.assertEqual(by_id["p1"]["candidate_personids"], "1001")
            self.assertEqual(by_id["p2"]["level"], "C")
            self.assertEqual(by_id["p3"]["level"], "B")
            self.assertEqual(by_id["p3"]["candidate_personids"], "1002")
            text = summary.read_text(encoding="utf-8")
            self.assertIn("L1 精确命中", text)
            self.assertIn("MQWW 诗人记录数", text)
            self.assertIn("未命中 (D)", text)

    def test_missing_db_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            rc = mm.main(["--db", str(td / "nope.db"),
                          "--mqww-poet", str(td / "nope.csv")])
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
