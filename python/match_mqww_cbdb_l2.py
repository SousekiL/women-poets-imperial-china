#!/usr/bin/env python3
"""只读 MQWW→CBDB L2 别名召回管线。

L2 只处理 L1 未命中、且非 L0 泛称的 MQWW 记录；别名命中永远标记为
review_*，不会自动提升为 A。SQLite 以 mode=ro + query_only 打开，唯一
默认产物是 data/derived/person_matches_l2_candidates.csv 与摘要文件。
"""
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from collections import defaultdict, Counter
from pathlib import Path

from match_mqww_cbdb import (CBDB_DB_DEFAULT, MQWW_POET_DEFAULT,
                             OUT_DEFAULT as L1_DEFAULT, classify_l0)

OUT_DEFAULT = "data/derived/person_matches_l2_candidates.csv"
SUMMARY_DEFAULT = "data/derived/match_l2_summary.txt"
ALIAS_FIELDS = ("ZiHZ", "HaoHZ", "OtherZiHaoHZ")
HEADER = ["poetID", "NameHZ", "ZiHZ", "HaoHZ", "OtherZiHaoHZ",
          "level_l1", "alias_values", "candidate_personids", "candidate_names",
          "candidate_sources", "candidate_female_flags", "n_candidates",
          "n_female_candidates", "status"]


def split_aliases(value: str) -> list[str]:
    """Split comma/Chinese-comma separated MQWW alias cells, preserving text."""
    return [x.strip() for x in re.split(r"[,，;；]", value or "") if x.strip()]


def load_csv(path: str | Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_alias_index(conn: sqlite3.Connection, aliases: set[str]) -> dict[str, list[tuple[str, str]]]:
    """Return alias -> [(personid, source)] from ALTNAME_DATA and NAME_LIST."""
    out: dict[str, set[tuple[str, str]]] = defaultdict(set)
    values = sorted(a for a in aliases if a)
    for table, col, source in (("ALTNAME_DATA", "c_alt_name_chn", "ALTNAME_DATA"),
                               ("CBDB_NAME_LIST", "name", "CBDB_NAME_LIST")):
        for i in range(0, len(values), 500):
            chunk = values[i:i + 500]
            marks = ",".join("?" for _ in chunk)
            sql = f"SELECT c_personid, {col} FROM {table} WHERE {col} IN ({marks})"
            for pid, alias in conn.execute(sql, chunk):
                if alias and str(alias).strip() in aliases:
                    out[str(alias).strip()].add((str(pid), source))
    return {a: sorted(v, key=lambda x: (int(x[0]) if x[0].isdigit() else x[0], x[1]))
            for a, v in out.items()}


def load_people(conn: sqlite3.Connection, person_ids: set[str]) -> dict[str, tuple[str, bool, str, str]]:
    out = {}
    ids = sorted(person_ids, key=lambda x: int(x) if x.isdigit() else x)
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        marks = ",".join("?" for _ in chunk)
        sql = ("SELECT c_personid,c_name_chn,c_female,c_fl_earliest_year,"
               "c_fl_latest_year FROM BIOG_MAIN WHERE c_personid IN (" + marks + ")")
        for pid, name, female, earliest, latest in conn.execute(sql, chunk):
            out[str(pid)] = (str(name or ""), bool(female), str(earliest or ""), str(latest or ""))
    return out


def match_l2(poets, baseline, alias_index, people):
    rows = []
    for poet in poets:
        pid = poet.get("poetID", "").strip()
        base = baseline.get(pid, {})
        name = (poet.get("NameHZ") or "").strip()
        aliases = []
        for field in ALIAS_FIELDS:
            aliases.extend(split_aliases(poet.get(field, "")))
        aliases = list(dict.fromkeys(aliases))
        candidates = {}
        for alias in aliases:
            for person, source in alias_index.get(alias, []):
                candidates.setdefault(person, set()).add(source)
        details = [(person, people[person], sorted(sources)) for person, sources in candidates.items() if person in people]
        details.sort(key=lambda x: (x[0]))
        female = [x for x in details if x[1][1]]
        if base.get("level") in ("A", "B"):
            status = "existing_l1_match"
        elif base.get("level") == "C" or classify_l0(name):
            status = "skip_l0"
        elif not aliases:
            status = "no_alias_value"
        elif not details:
            status = "no_alias_match"
        elif len(details) > 1:
            status = "review_multi_candidate"
        elif female:
            status = "review_unique_female"
        else:
            status = "review_unique_nonfemale"
        rows.append({
            "poetID": pid, "NameHZ": name,
            "ZiHZ": poet.get("ZiHZ", "").strip(), "HaoHZ": poet.get("HaoHZ", "").strip(),
            "OtherZiHaoHZ": poet.get("OtherZiHaoHZ", "").strip(),
            "level_l1": base.get("level", ""), "alias_values": "|".join(aliases),
            "candidate_personids": "|".join(x[0] for x in details),
            "candidate_names": "|".join(x[1][0] for x in details),
            "candidate_sources": "|".join(x[0] + ":" + "+".join(x[2]) for x in details),
            "candidate_female_flags": "|".join("1" if x[1][1] else "0" for x in details),
            "n_candidates": str(len(details)), "n_female_candidates": str(len(female)),
            "status": status,
        })
    return rows


def write_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER); w.writeheader(); w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=CBDB_DB_DEFAULT)
    ap.add_argument("--mqww-poet", default=MQWW_POET_DEFAULT)
    ap.add_argument("--baseline", default=L1_DEFAULT)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--summary-out", default=SUMMARY_DEFAULT)
    args = ap.parse_args(argv)
    poets = load_csv(args.mqww_poet)
    baseline_rows = load_csv(args.baseline)
    baseline = {r["poetID"]: r for r in baseline_rows}
    conn = sqlite3.connect(f"file:{Path(args.db).expanduser().resolve()}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        aliases = {a for p in poets for f in ALIAS_FIELDS for a in split_aliases(p.get(f, ""))}
        index = load_alias_index(conn, aliases)
        people = load_people(conn, {pid for vals in index.values() for pid, _ in vals})
    finally:
        conn.close()
    rows = match_l2(poets, baseline, index, people)
    write_csv(args.out, rows)
    counts = Counter(r["status"] for r in rows)
    candidate_rows = sum(r["n_candidates"] != "0" and r["status"] not in ("existing_l1_match", "skip_l0") for r in rows)
    summary = ["MQWW -> CBDB L2 别名召回摘要（只读）", f"records={len(rows)}", f"unique_alias_values={len(aliases)}",
               f"alias_values_with_hits={len(index)}", f"candidate_records={candidate_rows}"]
    summary.extend(f"{k}={v}" for k, v in sorted(counts.items()))
    Path(args.summary_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary_out).write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("输出 L2 CSV:", Path(args.out).resolve()); print("输出摘要:", Path(args.summary_out).resolve())
    for k, v in sorted(counts.items()): print(f"{k:28s} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
