#!/usr/bin/env python3
"""MQWW 女性关系网络派生数据构建（只读）。

输入（data/derived/）
  person_matches_baseline.csv        L0/L1 匹配基线（A 级=唯一女性候选）
  person_matches_l2_candidates.csv   L2 别名候选（节点富集用）

外部原始数据（只读 URI，不写原库）
  CBDB cbdb202409.db                 BIOG_MAIN / KIN_DATA / ASSOC_DATA /
                                     KINSHIP_CODES / ASSOC_CODES
  MQWW cycle/ work.csv, workpoetlinks.csv, poempoetlinks.csv, workpoemlinks.csv

输出（data/derived/network/，仅派生数据）
  network_nodes.csv          人物节点（CBDB 人物 + MQWW 诗人）
  direct_edges.csv           直接关系边（A 级女性的 CBDB 亲属/社会关系）
  work_nodes.csv             作品节点（MQWW 文献）
  work_person_edges.csv      作品—人物二部边（直接 + 经诗作传递）

关系类型不猜测：亲属/社会关系标签取自 KINSHIP_CODES.c_kinrel_chn 与
ASSOC_CODES.c_assoc_desc_chn（真实 code 表）；方向仅按记录方向标注，
不做语义方向推断。

用法
  python3 python/build_network_derived.py [--limit N]   # --limit 小样本验证
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DERIVED = REPO / "data" / "derived"
NET_OUT = DERIVED / "network"
CBDB_DB = Path(
    "/Users/sousekilyu/Documents/Data/biography_literature_CBDB_china_historical/"
    "cbdb202409.db"
)
MQWW_CYCLE = Path(
    "/Users/sousekilyu/Documents/Data/biography_literature_CBDB_china_historical/"
    "mqww_mingqing_women_writings/cycle"
)

CONF = {
    "match_A": 0.9,        # 唯一女性候选（基线 A 级）
    "match_B_f": 0.6,      # 女性标记但多候选/待消歧
    "match_B_nf": 0.3,     # 命中但非女性标记
    "relation_cbdb": 1.0,  # CBDB 显式关系记录本身
    "work_direct": 1.0,    # MQWW 显式 work-poet 链接
    "work_via_poem": 0.8,  # work-poem-poet 传递边
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_baseline() -> dict[str, dict]:
    """poetID -> {level, matched, personid (A 级唯一 id), female_flagged}"""
    out: dict[str, dict] = {}
    for r in read_csv(DERIVED / "person_matches_baseline.csv"):
        pid = r["poetID"]
        level = r["level"]
        personid = ""
        if r["matched"] == "1" and r["n_candidates"] == "1":
            personid = r["candidate_personids"]
        out[pid] = {
            "level": level,
            "matched": r["matched"],
            "personid": personid,
            "female_flagged": r["female_flagged"],
            "name_hz": r["NameHZ"],
        }
    return out


def load_l2() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in read_csv(DERIVED / "person_matches_l2_candidates.csv"):
        out[r["poetID"]] = {
            "status": r["status"],
            "candidate_personids": r["candidate_personids"],
            "candidate_sources": r["candidate_sources"],
            "n_candidates": r["n_candidates"],
            "n_female_candidates": r["n_female_candidates"],
        }
    return out


def connect_cbdb() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{CBDB_DB}?mode=ro", uri=True)
    conn.execute("PRAGMA query_only=ON")
    return conn


def load_code_tables(conn):
    kin = {str(r[0]): r for r in conn.execute(
        "SELECT c_kincode, c_kinrel_chn, c_kinrel FROM KINSHIP_CODES")}
    assoc = {str(r[0]): r for r in conn.execute(
        "SELECT c_assoc_code, c_assoc_desc_chn, c_assoc_desc FROM ASSOC_CODES")}
    return kin, assoc


def match_conf(level: str, female_flagged: str) -> float:
    if level == "A":
        return CONF["match_A"]
    if level == "B":
        return CONF["match_B_f"] if female_flagged == "1" else CONF["match_B_nf"]
    return 0.0


def fetch_names(conn, ids: set[str]) -> dict[str, str]:
    if not ids:
        return {}
    q = "SELECT c_personid, c_name_chn FROM BIOG_MAIN WHERE c_personid IN (%s)" % (
        ",".join("?" * len(ids))
    )
    return {str(pid): (name or "") for pid, name in conn.execute(q, sorted(ids))}


def build_nodes(baseline: dict, l2: dict, a_ids: set[str],
                kin_ids: set[str], assoc_ids: set[str], names: dict[str, str]):
    """person 节点：A 级女性 + 相关 CBDB 人物 + MQWW 诗人。"""
    nodes: dict[str, dict] = {}

    def add(node_id, **kw):
        nodes.setdefault(node_id, {
            "node_id": node_id, "cbdb_personid": "", "mqww_poetid": "",
            "name_chn": "", "name_hz": "", "is_female_flagged": "",
            "match_level": "", "in_cbdb_network": "0", "in_work_network": "0",
            "confidence": "", "source_layer": "",
        })
        nodes[node_id].update(kw)

    # A 级女性（CBDB 主节点）
    for pid, b in baseline.items():
        if b["level"] == "A" and b["personid"]:
            add(f"cbdb:{b['personid']}", cbdb_personid=b["personid"],
                mqww_poetid=pid, name_chn=names.get(b["personid"], ""),
                name_hz=b["name_hz"], is_female_flagged="1",
                match_level="A", in_cbdb_network="1", in_work_network="1",
                confidence=str(CONF["match_A"]), source_layer="cbdb+mqww")
        elif b["level"] == "B" and b["personid"]:
            add(f"cbdb:{b['personid']}", cbdb_personid=b["personid"],
                mqww_poetid=pid, name_chn=names.get(b["personid"], ""),
                name_hz=b["name_hz"], is_female_flagged=b["female_flagged"],
                match_level="B", in_cbdb_network="0", in_work_network="1",
                confidence=str(match_conf("B", b["female_flagged"])),
                source_layer="cbdb+mqww")
        elif b["level"] in ("B", "D", "C"):
            # 无唯一 CBDB id 的 MQWW 诗人：节点落在 work 网络
            add(f"mqww:{pid}", mqww_poetid=pid, name_hz=b["name_hz"],
                is_female_flagged=b["female_flagged"] if b["level"] != "C" else "",
                match_level=b["level"], in_cbdb_network="0", in_work_network="1",
                confidence=str(match_conf(b["level"], b["female_flagged"])),
                source_layer="mqww")

    # 相关 CBDB 人物（kin/assoc 对端）
    for cid in kin_ids | assoc_ids:
        if cid in a_ids:
            continue
        add(f"cbdb:{cid}", cbdb_personid=cid, name_chn=names.get(cid, ""),
            match_level="", in_cbdb_network="1", in_work_network="0",
            confidence=str(CONF["relation_cbdb"]), source_layer="cbdb")
    return nodes


def build_direct_edges(conn, a_ids: set[str], kin: dict, assoc: dict,
                       a_poet_map: dict[str, str]):
    """A 级女性的 KIN_DATA / ASSOC_DATA 直接关系（双向入射）。"""
    edges: list[dict] = []
    seen: set[tuple] = set()
    if not a_ids:
        return edges
    in_q = ",".join("?" * len(a_ids))
    id_list = sorted(a_ids)

    # 亲属：记录方向 + 反向
    for row in conn.execute(
            f"SELECT c_personid, c_kin_id, c_kin_code FROM KIN_DATA "
            f"WHERE c_personid IN ({in_q})", id_list):
        src, tgt, code = str(row[0]), str(row[1]), str(row[2])
        if tgt == "-10000" or tgt == "-1" or src == tgt:
            continue
        key = (src, tgt, code, "kin")
        if key in seen:
            continue
        seen.add(key)
        edges.append(_edge(src, tgt, code, "kin", kin, "cbdb_kin_direct",
                           a_poet_map))
    for row in conn.execute(
            f"SELECT c_personid, c_kin_id, c_kin_code FROM KIN_DATA "
            f"WHERE c_kin_id IN ({in_q})", id_list):
        src, tgt, code = str(row[0]), str(row[1]), str(row[2])
        if src == "-10000" or src == "-1" or src == tgt:
            continue
        key = (src, tgt, code, "kin")
        if key in seen:
            continue
        seen.add(key)
        edges.append(_edge(src, tgt, code, "kin", kin, "cbdb_kin_reverse",
                           a_poet_map))

    # 社会关系：记录方向 + 反向
    for row in conn.execute(
            f"SELECT c_personid, c_assoc_id, c_assoc_code FROM ASSOC_DATA "
            f"WHERE c_personid IN ({in_q})", id_list):
        src, tgt, code = str(row[0]), str(row[1]), str(row[2])
        if tgt in ("-10000", "-1") or src == tgt:
            continue
        key = (src, tgt, code, "assoc")
        if key in seen:
            continue
        seen.add(key)
        edges.append(_edge(src, tgt, code, "assoc", assoc, "cbdb_assoc_direct",
                           a_poet_map))
    for row in conn.execute(
            f"SELECT c_personid, c_assoc_id, c_assoc_code FROM ASSOC_DATA "
            f"WHERE c_assoc_id IN ({in_q})", id_list):
        src, tgt, code = str(row[0]), str(row[1]), str(row[2])
        if src in ("-10000", "-1") or src == tgt:
            continue
        key = (src, tgt, code, "assoc")
        if key in seen:
            continue
        seen.add(key)
        edges.append(_edge(src, tgt, code, "assoc", assoc, "cbdb_assoc_reverse",
                           a_poet_map))
    return edges


def _edge(src, tgt, code, kind, codes, rule, a_poet_map):
    label = ""
    if kind == "kin" and code in codes:
        label = codes[code][1] or ""
    elif kind == "assoc" and code in codes:
        label = codes[code][1] or ""
    person_in = src if src in a_poet_map else tgt
    return {
        "edge_id": "", "source_node_id": f"cbdb:{src}",
        "target_node_id": f"cbdb:{tgt}", "relation_code": code,
        "relation_code_type": kind, "relation_label_chn": label,
        "direction": "recorded" if src in a_poet_map else "reversed",
        "source_record_id": person_in,
        "source_layer": f"cbdb_{kind}",
        "confidence": str(CONF["relation_cbdb"] * CONF["match_A"]),
        "derivation_rule": rule,
        "source_match_level": "A",
    }


def build_work_data():
    """work 节点 + work-person 边（direct + via poem）。"""
    work_rows = read_csv(MQWW_CYCLE / "work.csv")
    work_meta = {r["workID"]: r for r in work_rows}

    wpl = read_csv(MQWW_CYCLE / "workpoetlinks.csv")
    wpl_meta = {r["workID"]: r for r in wpl}
    ppl = read_csv(MQWW_CYCLE / "poempoetlinks.csv")
    poem_to_poet = {r["poemID"]: r["poetID"] for r in ppl}
    wpln = read_csv(MQWW_CYCLE / "workpoemlinks.csv")

    work_nodes: dict[str, dict] = {}
    edges: list[dict] = []
    seen: set[tuple] = set()

    def add_work(wid):
        if wid in work_nodes:
            return
        m = work_meta.get(wid, {})
        work_nodes[wid] = {
            "work_id": wid, "title_hz": m.get("TitleHZ", ""),
            "title_py": m.get("TitlePY", ""), "worktype": m.get("worktype", ""),
            "number_juan": m.get("NumberJuan", ""),
            "pub_year": m.get("DateXF", ""),
            "n_poems": str(sum(1 for r in wpln if r["workID"] == wid)),
        }

    def add_edge(eid, wid, poem_id, poet_id, role, rule, layer, conf,
                 source_record_id):
        key = (wid, poet_id, poem_id, rule)
        if key in seen:
            return
        seen.add(key)
        add_work(wid)
        edges.append({
            "edge_id": eid, "work_id": wid, "poem_id": poem_id,
            "poet_id": poet_id, "role": role,
            "source_layer": layer, "confidence": str(conf),
            "derivation_rule": rule, "source_record_id": source_record_id,
        })

    # 直接：workpoetlinks（work -> poet，含 role 如 作者/序作者）
    for r in wpl:
        add_edge(f"wpe_direct_{r['wcID']}", r["workID"], "", r["poetID"],
                 r.get("role", ""), "mqww_work_direct",
                 "mqww_work_direct", CONF["work_direct"], r["wcID"])

    # 传递：workpoemlinks + poempoetlinks（work -> poem -> poet）
    for r in wpln:
        wid, pmid = r["workID"], r["poemID"]
        poet = poem_to_poet.get(pmid, "")
        if not poet:
            continue
        add_edge(f"wpe_via_poem_{r['wpID']}_{pmid}", wid, pmid, poet, "",
                 "mqww_work_via_poem", "mqww_work_via_poem",
                 CONF["work_via_poem"], f"{r['wpID']}:{pmid}")

    return work_nodes, edges


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0,
                    help="仅处理前 N 个 A 级人物（小样本验证）")
    args = ap.parse_args(argv)

    baseline = load_baseline()
    l2 = load_l2()
    a_persons = {b["personid"] for b in baseline.values()
                 if b["level"] == "A" and b["personid"]}
    a_poet_map = {b["personid"]: pid for pid, b in baseline.items()
                  if b["level"] == "A" and b["personid"]}
    print(f"A 级匹配女性: {len(a_persons)}")
    if args.limit:
        a_persons = set(sorted(a_persons)[: args.limit])
        a_poet_map = {p: a_poet_map[p] for p in a_persons}
        print(f"[小样本] 限制为前 {len(a_persons)} 个")

    conn = connect_cbdb()
    try:
        kin, assoc = load_code_tables(conn)
        edges = build_direct_edges(conn, a_persons, kin, assoc, a_poet_map)
        related_ids = {e["source_node_id"][5:] for e in edges}
        related_ids |= {e["target_node_id"][5:] for e in edges}
        related_ids -= a_persons
        names = fetch_names(conn, related_ids | a_persons)
    finally:
        conn.close()

    nodes = build_nodes(baseline, l2, a_persons, related_ids, related_ids, names)
    work_nodes, work_edges = build_work_data()

    # work 边补 person 节点映射与 match_level
    work_edges_out = []
    for e in work_edges:
        b = baseline.get(e["poet_id"], {})
        # 优先 cbdb 节点（A/B 且唯一 id），否则 mqww 节点
        if b and b["personid"]:
            person_node = f"cbdb:{b['personid']}"
        else:
            person_node = f"mqww:{e['poet_id']}"
        e["person_node_id"] = person_node
        e["poet_match_level"] = b.get("level", "") if b else ""
        work_edges_out.append(e)

    # 补节点：work 边引用了 poet.csv 中不存在的 poetID（孤儿诗人）
    for e in work_edges_out:
        nid = e["person_node_id"]
        if nid not in nodes:
            nodes[nid] = {
                "node_id": nid, "node_type": "person",
                "cbdb_personid": "", "mqww_poetid": e["poet_id"],
                "name_chn": "", "name_hz": "",
                "is_female_flagged": "", "match_level": "",
                "in_cbdb_network": "0", "in_work_network": "1",
                "confidence": "0.0", "source_layer": "mqww",
            }

    # 写文件
    NET_OUT.mkdir(parents=True, exist_ok=True)
    ncols = ["node_id", "node_type", "cbdb_personid", "mqww_poetid", "name_chn",
             "name_hz", "is_female_flagged", "match_level", "in_cbdb_network",
             "in_work_network", "confidence", "source_layer"]
    for n in nodes.values():
        n["node_type"] = "person"
    write_csv(NET_OUT / "network_nodes.csv", list(nodes.values()), ncols)

    ecols = ["edge_id", "source_node_id", "target_node_id", "relation_code",
             "relation_code_type", "relation_label_chn", "direction",
             "source_record_id", "source_layer", "confidence",
             "derivation_rule", "source_match_level"]
    for i, e in enumerate(edges):
        e["edge_id"] = f"de_{i}"
    write_csv(NET_OUT / "direct_edges.csv", edges, ecols)

    wcols = ["work_id", "title_hz", "title_py", "worktype", "number_juan",
             "pub_year", "n_poems"]
    write_csv(NET_OUT / "work_nodes.csv", list(work_nodes.values()), wcols)

    wecols = ["edge_id", "work_id", "poem_id", "poet_id", "role",
              "person_node_id", "poet_match_level", "source_layer",
              "confidence", "derivation_rule", "source_record_id"]
    write_csv(NET_OUT / "work_person_edges.csv", work_edges_out, wecols)

    n_kin = sum(1 for e in edges if e["relation_code_type"] == "kin")
    n_assoc = sum(1 for e in edges if e["relation_code_type"] == "assoc")
    n_direct = sum(1 for e in work_edges if "direct" in e["derivation_rule"])
    n_via = sum(1 for e in work_edges if "via_poem" in e["derivation_rule"])
    print(f"person 节点:        {len(nodes)}")
    print(f"direct 边:          {len(edges)} (kin {n_kin}, assoc {n_assoc})")
    print(f"work 节点:          {len(work_nodes)}")
    print(f"work-person 边:     {len(work_edges)} (direct {n_direct}, via_poem {n_via})")
    print(f"输出目录:           {NET_OUT}")
    return 0


def write_csv(path: Path, rows: list[dict], cols: list[str]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    sys.exit(main())
