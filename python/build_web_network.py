#!/usr/bin/env python3
"""Build compact, static web payloads from research-facing network CSV exports."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "data" / "derived" / "network"
OUT = REPO / "data" / "web-network"


def rows(name: str):
    with (SOURCE / name).open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def write_json(path: Path, value) -> dict:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    return {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def normalized_name(value: str) -> str:
    """Compare literal personal names without silently folding variants."""
    return re.sub(r"^(?:明|清|民國|民国)", "", (value or "").strip())


def title_authors(title: str) -> list[str]:
    """Extract literal names immediately preceding 撰 from an MQWW title."""
    matches = re.findall(r"([\u3400-\u9fff、，,]{1,24})撰", title or "")
    names = []
    for match in matches:
        for name in re.split(r"[、，,]", normalized_name(match)):
            name = name.removesuffix("等").strip()
            if 2 <= len(name) <= 8 and name not in names:
                names.append(name)
    return names


def build(source: Path = SOURCE, out: Path = OUT) -> dict:
    global SOURCE
    previous = SOURCE
    SOURCE = source
    try:
        people = [{
            "id": r["node_id"], "c": r["cbdb_personid"], "m": r["mqww_poetid"],
            "n": r["name_chn"], "h": r["name_hz"], "f": r["is_female_flagged"],
            "l": r["match_level"], "q": r["confidence"], "s": r["source_layer"],
        } for r in rows("network_nodes.csv")]
        direct = [{
            "id": r["edge_id"], "a": r["source_node_id"], "b": r["target_node_id"],
            "k": r["relation_code_type"], "code": r["relation_code"],
            "label": r["relation_label_chn"], "dir": r["direction"],
            "record": r["source_record_id"], "layer": r["source_layer"],
            "q": r["confidence"], "rule": r["derivation_rule"], "match": r["source_match_level"],
        } for r in rows("direct_edges.csv")]
        degree = Counter()
        for edge in direct:
            degree[edge["a"]] += 1
            degree[edge["b"]] += 1
        works = [{
            "id": r["work_id"], "t": r["title_hz"], "p": r["title_py"],
            "type": r["worktype"], "juan": r["number_juan"],
            "year": r["pub_year"], "poems": r["n_poems"],
        } for r in rows("work_nodes.csv")]
        grouped = defaultdict(list)
        layer_counts = Counter()
        total_work_edges = 0
        for r in rows("work_person_edges.csv"):
            layer = "work_direct" if r["derivation_rule"] == "mqww_work_direct" else "work_via_poem"
            grouped[r["work_id"]].append({
                "id": r["edge_id"], "person": r["person_node_id"], "poem": r["poem_id"],
                "poet": r["poet_id"], "role": r["role"], "layer": layer,
                "q": r["confidence"], "rule": r["derivation_rule"],
                "record": r["source_record_id"], "match": r["poet_match_level"],
            })
            layer_counts[layer] += 1
            total_work_edges += 1

        people_by_id = {person["id"]: person for person in people}
        author_index = {}
        for work in works:
            resolved = []
            for title_author in title_authors(work["t"]):
                candidates = []
                for edge in grouped.get(work["id"], []):
                    if edge["role"] not in {"主要作者", "作者"}:
                        continue
                    person = people_by_id.get(edge["person"])
                    if person and title_author in {normalized_name(person["n"]), normalized_name(person["h"])}:
                        candidates.append(edge["person"])
                for person_id in sorted(set(candidates)):
                    if person_id not in resolved:
                        resolved.append(person_id)
                        entry = author_index.setdefault(person_id, {
                            "id": person_id,
                            "name": people_by_id[person_id]["h"] or people_by_id[person_id]["n"],
                            "works": [],
                        })
                        entry["works"].append(work["id"])
            work["authors"] = resolved

        if out.exists():
            for old in (out / "works").glob("*.json"):
                old.unlink()
        files = {}
        people_fields = ["id", "c", "m", "n", "h", "f", "l", "q", "s"]
        direct_fields = ["id", "a", "b", "k", "code", "label", "dir", "record", "layer", "q", "rule", "match"]
        work_fields = ["id", "t", "p", "type", "juan", "year", "poems", "authors"]
        core = {"schema":"web-network-v1", "people_fields":people_fields,
                "people":[[item[field] for field in people_fields] for item in people],
                "direct_fields":direct_fields,
                "direct":[[item[field] for field in direct_fields] for item in direct],
                "work_fields":work_fields,
                "works":[[item[field] for field in work_fields] for item in works],
                "authors": sorted(author_index.values(), key=lambda item: (item["name"], item["id"])),
                "featured":[node_id for node_id, _ in degree.most_common(600)]}
        files["core.json"] = write_json(out / "core.json", core)
        work_index = {}
        for work in works:
            work_id = work["id"]
            edges = grouped.get(work_id, [])
            relative = f"works/{work_id}.json"
            files[relative] = write_json(out / relative, {"schema":"web-network-work-v1", "work":work_id, "edges":edges})
            work_index[work_id] = {"file":relative, "edges":len(edges),
                                   "work_direct":sum(e["layer"] == "work_direct" for e in edges),
                                   "work_via_poem":sum(e["layer"] == "work_via_poem" for e in edges)}
        manifest = {
            "schema":"web-network-manifest-v1",
            "generated_from":"data/derived/network/*.csv",
            "core":"core.json", "works":work_index,
            "counts":{"people":len(people), "works":len(works), "direct":len(direct),
                      "kin":sum(e["k"] == "kin" for e in direct),
                      "assoc":sum(e["k"] == "assoc" for e in direct),
                      "work_edges":total_work_edges, **layer_counts},
            "files":files,
        }
        write_json(out / "manifest.json", manifest)
        return manifest
    finally:
        SOURCE = previous


if __name__ == "__main__":
    manifest = build()
    print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))
