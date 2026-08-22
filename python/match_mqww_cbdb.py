#!/usr/bin/env python3
"""MQWW → CBDB 只读姓名匹配管线（L0 泛称排除 + L1 精确匹配基线）。

只读约束
--------
- CBDB SQLite 通过 ``file:<path>?mode=ro`` 只读 URI 打开，并额外执行
  ``PRAGMA query_only=ON``；任何对原库的写入都会失败。
- 不复制原始数据；唯一输出为派生 CSV（默认 ``data/derived/person_matches_baseline.csv``）
  与摘要文本（默认 ``data/derived/match_baseline_summary.txt``）。

分层（详见 docs/matching_method.md）
------------------------------------
- L0：泛称排除（「X氏」「無名氏」等无唯一标识姓名），记为 level=C。
- L1：NameHZ == BIOG_MAIN.c_name_chn 精确匹配；按女性标记与候选唯一性分级：
  - A：精确命中且恰 1 个候选且该候选 c_female=1（高置信）。
  - B：命中但非女性标记，或存在多个候选（需消歧/复核）。
  - D：未命中。C：L0 排除。

用法
----
    python3 python/match_mqww_cbdb.py [--db PATH] [--mqww-poet PATH]
                                      [--out PATH] [--summary-out PATH]

默认路径指向外部原始数据（只读引用）。输出为派生数据，可安全提交/分享。
依赖：仅 Python 标准库（sqlite3, csv, argparse, re, pathlib）。
"""
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

CBDB_DB_DEFAULT = (
    "/Users/sousekilyu/Documents/Data/biography_literature_CBDB_china_historical/"
    "cbdb202409.db"
)
MQWW_POET_DEFAULT = (
    "/Users/sousekilyu/Documents/Data/biography_literature_CBDB_china_historical/"
    "mqww_mingqing_women_writings/cycle/poet.csv"
)
OUT_DEFAULT = "data/derived/person_matches_baseline.csv"
SUMMARY_DEFAULT = None

# 泛称：单字/复姓 + 「氏」结尾（王氏、歐陽氏、王張氏），以及 無名氏/佚名/閨秀 等。
GENERIC_RE = re.compile(r"^(?:無名氏|佚名|閨秀|某某)$|^.{1,3}氏$")

OUT_HEADER = [
    "poetID", "NameHZ", "StartYear", "EndYear", "sex",
    "level", "reason", "matched",
    "n_candidates", "n_female_candidates", "female_flagged",
    "candidate_personids", "female_candidate_personids",
]


def classify_l0(name: str) -> str:
    """返回 L0 排除原因；非泛称返回空字符串。"""
    name = (name or "").strip()
    if not name:
        return "blank_name"
    if GENERIC_RE.match(name):
        return "generic_name"
    return ""


def load_poets(path: str | Path) -> list[dict[str, str]]:
    """读取 MQWW poet.csv（utf-8-sig），返回行字典列表。"""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def build_index(conn: sqlite3.Connection):
    """从 BIOG_MAIN 构建 {c_name_chn -> [(c_personid, c_female)]} 索引。

    返回 (index, 总行数, 女性行数)。名称为空/纯空白不进入索引。
    """
    cur = conn.execute(
        "SELECT c_personid, c_name_chn, c_female FROM BIOG_MAIN"
    )
    index: dict[str, list[tuple[str, bool]]] = {}
    n_total = 0
    n_female = 0
    for pid, name, female in cur:
        n_total += 1
        if female:
            n_female += 1
        key = (name or "").strip()
        if key:
            index.setdefault(key, []).append((str(pid), bool(female)))
    return index, n_total, n_female


def match_poets(
    poets: list[dict[str, str]], index: dict[str, list[tuple[str, bool]]]
) -> list[dict[str, str]]:
    """L0 + L1 匹配，返回输出行字典。"""
    rows: list[dict[str, str]] = []
    for p in poets:
        poet_id = p.get("poetID", "").strip()
        name = (p.get("NameHZ") or "").strip()
        start = (p.get("StartYear") or "").strip()
        end = (p.get("EndYear") or "").strip()
        sex = (p.get("Sex") or "").strip()

        reason = classify_l0(name)
        if reason:
            rows.append({
                "poetID": poet_id, "NameHZ": name, "StartYear": start,
                "EndYear": end, "sex": sex, "level": "C", "reason": reason,
                "matched": "0", "n_candidates": "0", "n_female_candidates": "0",
                "female_flagged": "0", "candidate_personids": "",
                "female_candidate_personids": "",
            })
            continue

        cands = index.get(name, [])
        if not cands:
            rows.append({
                "poetID": poet_id, "NameHZ": name, "StartYear": start,
                "EndYear": end, "sex": sex, "level": "D", "reason": "no_cbdb_name",
                "matched": "0", "n_candidates": "0", "n_female_candidates": "0",
                "female_flagged": "0", "candidate_personids": "",
                "female_candidate_personids": "",
            })
            continue

        n_cands = len(cands)
        n_female_cands = sum(1 for _, f in cands if f)
        female_flagged = n_female_cands >= 1
        person_ids = [pid for pid, _ in cands]
        female_ids = [pid for pid, f in cands if f]

        if female_flagged and n_cands == 1:
            level, reason = "A", "unique_female"
        elif female_flagged:
            level, reason = "B", "multiple_candidates_with_female"
        else:
            level, reason = "B", "not_female_flagged"

        rows.append({
            "poetID": poet_id, "NameHZ": name, "StartYear": start,
            "EndYear": end, "sex": sex, "level": level, "reason": reason,
            "matched": "1", "n_candidates": str(n_cands),
            "n_female_candidates": str(n_female_cands),
            "female_flagged": "1" if female_flagged else "0",
            "candidate_personids": "|".join(person_ids),
            "female_candidate_personids": "|".join(female_ids),
        })
    return rows


def summarize(rows: list[dict[str, str]], n_cbdb_total: int,
              n_cbdb_female: int) -> dict[str, int]:
    s: dict[str, int] = {
        "mqww_poet_records": len(rows),
        "mqww_unique_names": len({r["NameHZ"] for r in rows}),
        "level_A": 0, "level_B": 0, "level_C": 0, "level_D": 0,
        "matched": 0, "female_flagged_matched": 0,
        "cbdb_rows": n_cbdb_total, "cbdb_female_rows": n_cbdb_female,
    }
    for r in rows:
        s[f"level_{r['level']}"] += 1
        if r["matched"] == "1":
            s["matched"] += 1
            if r["female_flagged"] == "1":
                s["female_flagged_matched"] += 1
    s["l1_hit_rate_pct"] = round(
        s["matched"] / s["mqww_poet_records"] * 100, 1
    ) if s["mqww_poet_records"] else 0
    s["female_hit_rate_pct"] = round(
        s["female_flagged_matched"] / s["mqww_poet_records"] * 100, 1
    ) if s["mqww_poet_records"] else 0
    return s


def write_csv(path: str | Path, rows: list[dict[str, str]]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=OUT_HEADER)
        w.writeheader()
        w.writerows(rows)


def write_summary(path: str | Path, s: dict[str, int],
                  db_path: str, mqww_path: str) -> None:
    lines = [
        "MQWW -> CBDB L0/L1 匹配基线（只读审计，2026-08-22）",
        f"CBDB: {db_path}",
        f"MQWW poet: {mqww_path}",
        "----------------------------------------",
        f"CBDB BIOG_MAIN 总行数:      {s['cbdb_rows']}",
        f"CBDB 女性行数 (c_female=1): {s['cbdb_female_rows']}",
        f"MQWW 诗人记录数:            {s['mqww_poet_records']}",
        f"MQWW 唯一 NameHZ:           {s['mqww_unique_names']}",
        f"L0 泛称/无名排除 (C):       {s['level_C']}",
        f"L1 精确命中 (A+B):          {s['matched']}  ({s['l1_hit_rate_pct']}%)",
        f"  其中 A 级 (唯一女性):     {s['level_A']}",
        f"  B 级 (待消歧/复核):       {s['level_B']}",
        f"  女性标记命中 (A+B 中):    {s['female_flagged_matched']}  ({s['female_hit_rate_pct']}%)",
        f"未命中 (D):                 {s['level_D']}",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=CBDB_DB_DEFAULT, help="CBDB SQLite 路径（只读）")
    ap.add_argument("--mqww-poet", default=MQWW_POET_DEFAULT, help="MQWW poet.csv 路径")
    ap.add_argument("--out", default=OUT_DEFAULT, help="派生匹配 CSV 输出路径")
    ap.add_argument("--summary-out", default=SUMMARY_DEFAULT,
                    help="可选摘要文本输出路径（默认不写入额外文件）")
    args = ap.parse_args(argv)

    db_path = Path(args.db).expanduser().resolve()
    if not db_path.exists():
        print(f"ERROR: CBDB 数据库不存在: {db_path}", file=sys.stderr)
        return 1
    mqww_path = Path(args.mqww_poet).expanduser().resolve()
    if not mqww_path.exists():
        print(f"ERROR: MQWW poet.csv 不存在: {mqww_path}", file=sys.stderr)
        return 1

    # 只读 URI + query_only 双保险：任何写入尝试都会抛 OperationalError。
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        index, n_cbdb_total, n_cbdb_female = build_index(conn)
    finally:
        conn.close()

    poets = load_poets(mqww_path)
    rows = match_poets(poets, index)
    stats = summarize(rows, n_cbdb_total, n_cbdb_female)

    write_csv(args.out, rows)
    if args.summary_out:
        write_summary(args.summary_out, stats, str(db_path), str(mqww_path))

    print(f"输出匹配 CSV:  {Path(args.out).resolve()}")
    if args.summary_out:
        print(f"输出摘要:      {Path(args.summary_out).resolve()}")
    for k, v in stats.items():
        print(f"{k:28s} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
