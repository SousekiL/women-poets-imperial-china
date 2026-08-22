#!/usr/bin/env python3
"""Read-only MQWW→CBDB L3 surname/given-name split candidate recall.

L3 runs only for records not already matched by L1 or recalled by L2. It compares
literal MQWW NameHZ splits with BIOG_MAIN.c_surname_chn/c_mingzi_chn. It performs
no variant-character folding and never creates relationship edges or upgrades an
A/B level: every hit is pending human review.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from match_mqww_cbdb import (CBDB_DB_DEFAULT, MQWW_POET_DEFAULT,
                             OUT_DEFAULT as L1_DEFAULT, classify_l0)
from match_mqww_cbdb_l2 import OUT_DEFAULT as L2_DEFAULT

OUT_DEFAULT = "data/derived/person_matches_l3_candidates.csv"
SUMMARY_DEFAULT = "data/derived/match_l3_summary.txt"
MANIFEST_DEFAULT = "data/derived/match_l3_manifest.json"
RULE_VERSION = "l3_split_name_v1"
CANDIDATE_SOURCE = "BIOG_MAIN.c_surname_chn+c_mingzi_chn"
HAN_NAME_RE = re.compile(r"^[㐀-鿿]{2,4}$")
HEADER = [
    "poetID", "NameHZ", "StartYear", "EndYear", "sex", "level_l1",
    "match_method", "candidate_source", "rule_version", "split_keys",
    "candidate_personids", "candidate_names", "candidate_female_flags",
    "n_candidates", "n_female_candidates", "prior_candidate_personids",
    "status", "reviewer_decision",
]


def load_csv(path: str | Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def split_name(name: str) -> list[tuple[str, str]]:
    """Return conservative literal one-/two-character surname splits.

    Only 2–4 CJK-character names are structurally eligible. No simplified/
    traditional or other variant normalization is performed.
    """
    value = (name or "").strip()
    if not HAN_NAME_RE.fullmatch(value):
        return []
    cuts = (1, 2) if len(value) >= 3 else (1,)
    return [(value[:cut], value[cut:]) for cut in cuts if value[cut:]]


def load_split_index(
    conn: sqlite3.Connection, wanted: set[tuple[str, str]]
) -> dict[tuple[str, str], list[tuple[str, str, bool]]]:
    """Load only requested literal split keys from read-only BIOG_MAIN."""
    out: dict[tuple[str, str], set[tuple[str, str, bool]]] = defaultdict(set)
    if not wanted:
        return {}
    sql = ("SELECT c_personid,c_name_chn,c_surname_chn,c_mingzi_chn,c_female "
           "FROM BIOG_MAIN WHERE c_surname_chn IS NOT NULL "
           "AND c_mingzi_chn IS NOT NULL")
    for personid, name, surname, given, female in conn.execute(sql):
        key = ((surname or "").strip(), (given or "").strip())
        if key[0] and key[1] and key in wanted:
            out[key].add((str(personid), str(name or "").strip(), bool(female)))
    keyfn = lambda row: (int(row[0]) if row[0].isdigit() else row[0], row[1])
    return {key: sorted(values, key=keyfn) for key, values in out.items()}


def recall_candidates(
    name: str, split_index: dict[tuple[str, str], list[tuple[str, str, bool]]]
) -> list[tuple[str, str, bool]]:
    """Recall and person-id deduplicate candidates across valid splits."""
    by_id: dict[str, tuple[str, str, bool]] = {}
    for key in split_name(name):
        for row in split_index.get(key, []):
            by_id.setdefault(row[0], row)
    return sorted(by_id.values(), key=lambda row: int(row[0]) if row[0].isdigit() else row[0])


def _ids(value: str) -> set[str]:
    return {item for item in (value or "").split("|") if item}


def match_l3(poets, baseline, l2_rows, split_index):
    rows = []
    for poet in poets:
        poet_id = (poet.get("poetID") or "").strip()
        name = (poet.get("NameHZ") or "").strip()
        base = baseline.get(poet_id, {})
        l2 = l2_rows.get(poet_id, {})
        l1_ids = _ids(base.get("candidate_personids", ""))
        l2_ids = _ids(l2.get("candidate_personids", ""))
        prior_ids = l1_ids | l2_ids
        reason = classify_l0(name)
        keys = split_name(name)

        if base.get("level") in ("A", "B"):
            status, candidates = "existing_l1_match", []
        elif base.get("level") == "C" or reason:
            status, candidates = "skip_l0", []
        elif l2_ids:
            status, candidates = "existing_l2_candidate", []
        elif not keys:
            status, candidates = "no_valid_split", []
        else:
            candidates = recall_candidates(name, split_index)
            status = "pending_human_review" if candidates else "no_split_match"

        female = [row for row in candidates if row[2]]
        rows.append({
            "poetID": poet_id, "NameHZ": name,
            "StartYear": (poet.get("StartYear") or "").strip(),
            "EndYear": (poet.get("EndYear") or "").strip(),
            "sex": (poet.get("Sex") or "").strip(),
            "level_l1": base.get("level", ""),
            "match_method": "l3_split_name" if candidates else "",
            "candidate_source": CANDIDATE_SOURCE if candidates else "",
            "rule_version": RULE_VERSION,
            "split_keys": "|".join(surname + "+" + given for surname, given in keys),
            "candidate_personids": "|".join(row[0] for row in candidates),
            "candidate_names": "|".join(row[1] for row in candidates),
            "candidate_female_flags": "|".join("1" if row[2] else "0" for row in candidates),
            "n_candidates": str(len(candidates)),
            "n_female_candidates": str(len(female)),
            "prior_candidate_personids": "|".join(sorted(prior_ids, key=lambda x: int(x) if x.isdigit() else x)),
            "status": status,
            "reviewer_decision": "pending_human_review" if candidates else "",
        })
    return rows


def summarize(rows):
    counts = Counter(row["status"] for row in rows)
    new_pairs = overlap_pairs = conflicts = candidate_records = 0
    for row in rows:
        current = _ids(row["candidate_personids"])
        prior = _ids(row.get("prior_candidate_personids", ""))
        if current:
            candidate_records += 1
            overlap_pairs += len(current & prior)
            new_pairs += len(current - prior)
            if prior and not current & prior:
                conflicts += 1
    stats = {
        "records": len(rows),
        "candidate_records": candidate_records,
        "new_candidate_pairs": new_pairs,
        "overlap_candidate_pairs": overlap_pairs,
        "conflict_records": conflicts,
    }
    stats.update({f"status_{key}": value for key, value in sorted(counts.items())})
    return stats


def write_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(path, stats, db, mqww, l1, l2, out):
    manifest = {
        "schema": "mqww_cbdb_l3_manifest_v1",
        "generated_by": "python/match_mqww_cbdb_l3.py",
        "rule_version": RULE_VERSION,
        "match_method": "l3_split_name",
        "candidate_source": CANDIDATE_SOURCE,
        "inputs": {"cbdb_sqlite": db, "mqww_poet_csv": mqww,
                   "l1_baseline_csv": l1, "l2_candidates_csv": l2,
                   "readonly": "sqlite mode=ro URI + PRAGMA query_only=ON"},
        "outputs": {"candidate_csv": out},
        "eligibility": "L1 unmatched, non-L0, and without an L2 candidate",
        "split_rule": "literal 2–4 CJK characters; cuts after character 1 and, when possible, 2",
        "variant_policy": "no variant/simplified/traditional folding; exact component equality only",
        "review_policy": "pending_human_review_only",
        "creates_relationship_edges": False,
        "precision": "not_evaluated_no_human_decisions",
        "recall": "not_evaluated_no_independent_gold_standard",
        "counts": stats,
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=CBDB_DB_DEFAULT)
    parser.add_argument("--mqww-poet", default=MQWW_POET_DEFAULT)
    parser.add_argument("--baseline", default=L1_DEFAULT)
    parser.add_argument("--l2", default=L2_DEFAULT)
    parser.add_argument("--out", default=OUT_DEFAULT)
    parser.add_argument("--summary-out", default=SUMMARY_DEFAULT)
    parser.add_argument("--manifest-out", default=MANIFEST_DEFAULT)
    args = parser.parse_args(argv)

    poets = load_csv(args.mqww_poet)
    baseline = {row["poetID"]: row for row in load_csv(args.baseline)}
    l2_rows = {row["poetID"]: row for row in load_csv(args.l2)}
    wanted = {key for poet in poets for key in split_name(poet.get("NameHZ", ""))}
    db_path = Path(args.db).expanduser().resolve()
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        split_index = load_split_index(conn, wanted)
    finally:
        conn.close()

    rows = match_l3(poets, baseline, l2_rows, split_index)
    stats = summarize(rows)
    write_csv(args.out, rows)
    write_manifest(args.manifest_out, stats, str(db_path), str(Path(args.mqww_poet).expanduser().resolve()),
                   args.baseline, args.l2, args.out)
    lines = ["MQWW -> CBDB L3 姓名拆分候选召回摘要（只读）",
             f"rule_version={RULE_VERSION}"] + [f"{key}={value}" for key, value in stats.items()]
    Path(args.summary_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary_out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("输出 L3 CSV:", Path(args.out).resolve())
    print("输出摘要:", Path(args.summary_out).resolve())
    print("输出 manifest:", Path(args.manifest_out).resolve())
    for key, value in stats.items():
        print(f"{key:32s} {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
