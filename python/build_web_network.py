#!/usr/bin/env python3
"""Build compact, static web payloads from research-facing network CSV exports."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "data" / "derived" / "network"
OUT = REPO / "data" / "web-network"
CHINESE_NUMBERS = ("一", "二", "三", "四", "五", "六", "七", "八", "九", "十")


def rows(name: str):
    with (SOURCE / name).open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def write_json(path: Path, value) -> dict:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    return {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def build(source: Path = SOURCE, out: Path = OUT) -> dict:
    global SOURCE
    previous = SOURCE
    SOURCE = source
    try:
        people = [{
            "id": r["node_id"], "c": r["cbdb_personid"], "m": r["mqww_poetid"],
            "n": r["name_chn"], "h": r["name_hz"], "f": r["is_female_flagged"],
            "g": "female" if r["is_female_flagged"] == "1" else ("male" if r["source_layer"] == "cbdb" and r["is_female_flagged"] == "0" else "unknown"),
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
        raw_works = list(rows("work_nodes.csv"))
        unknown_work_ids = sorted(
            (r["work_id"] for r in raw_works if not r["title_hz"].strip()),
            key=lambda work_id: int(work_id),
        )
        unknown_titles = {
            work_id: f"作品名不详{CHINESE_NUMBERS[number - 1]}"
            for number, work_id in enumerate(unknown_work_ids, start=1)
        }
        works = [{
            "id": r["work_id"], "t": r["title_hz"].strip() or unknown_titles[r["work_id"]], "p": r["title_py"],
            "type": r["worktype"], "juan": r["number_juan"],
            "year": r["pub_year"], "poems": r["n_poems"],
        } for r in raw_works]
        work_by_id = {work["id"]: work for work in works}
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

        if out.exists():
            for directory in ("works", "types"):
                for old in (out / directory).glob("*.json"):
                    old.unlink()
        files = {}
        people_fields = ["id", "c", "m", "n", "h", "f", "g", "l", "q", "s"]
        direct_fields = ["id", "a", "b", "k", "code", "label", "dir", "record", "layer", "q", "rule", "match"]
        work_fields = ["id", "t", "p", "type", "juan", "year", "poems"]
        core = {"schema":"web-network-v1", "people_fields":people_fields,
                "people":[[item[field] for field in people_fields] for item in people],
                "direct_fields":direct_fields,
                "direct":[[item[field] for field in direct_fields] for item in direct],
                "work_fields":work_fields,
                "works":[[item[field] for field in work_fields] for item in works],
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
        type_index = {}
        for type_name in ["__all__", *sorted({work["type"] for work in works})]:
            type_works = [work["id"] for work in works if type_name == "__all__" or work["type"] == type_name]
            compact = defaultdict(list)
            for work_id in type_works:
                for edge in grouped.get(work_id, []):
                    compact[(work_id, edge["person"], edge["layer"])].append(edge)
            edges = [{
                "id": f"type_{work_id}_{person}_{layer}", "work": work_id,
                "person": person, "layer": layer, "n": len(items),
                "role": items[0]["role"] if layer == "work_direct" else "",
                "record": items[0]["record"], "match": items[0]["match"],
            } for (work_id, person, layer), items in compact.items()]
            token = hashlib.sha256(type_name.encode("utf-8")).hexdigest()[:12]
            relative = f"types/{token}.json"
            files[relative] = write_json(out / relative, {
                "schema": "web-network-type-v1", "type": type_name,
                "works": type_works, "edges": edges,
            })
            type_index[type_name] = {"file": relative, "works": len(type_works), "edges": len(edges)}
        all_works = [work["id"] for work in works]
        all_compact = defaultdict(list)
        for work_id in all_works:
            for edge in grouped.get(work_id, []):
                all_compact[(work_id, edge["person"], edge["layer"])].append(edge)
        all_edges = [{
            "id": f"all_{work_id}_{person}_{layer}", "work": work_id,
            "person": person, "layer": layer, "n": len(items),
            "role": items[0]["role"] if layer == "work_direct" else "",
            "record": items[0]["record"], "match": items[0]["match"],
        } for (work_id, person, layer), items in all_compact.items()]
        all_relative = "types/all.json"
        files[all_relative] = write_json(out / all_relative, {
            "schema": "web-network-type-v1", "type": "全部作品",
            "works": all_works, "edges": all_edges,
        })
        all_index = {"file": all_relative, "works": len(all_works), "edges": len(all_edges)}
        manifest = {
            "schema":"web-network-manifest-v1",
            "generated_from":"data/derived/network/*.csv",
            "core":"core.json", "works":work_index, "types":type_index, "all":all_index,
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
