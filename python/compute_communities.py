#!/usr/bin/env python3
"""Reproducible community and descriptive time analysis for typed networks."""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
NETWORK_DIR = ROOT / "data" / "derived" / "network"
OUTPUT_DIR = ROOT / "data" / "derived" / "community"
NETWORK_VERSIONS = ("kin_typed_undirected", "assoc_typed_undirected")
DEFAULT_SEED = 20260822
DEFAULT_RESOLUTIONS = (1.0, 1.25)
MEMBER_FIELDS = (
    "network_version",
    "resolution",
    "community_id",
    "node_id",
    "community_size",
    "degree",
    "internal_degree",
    "external_degree",
    "within_community_degree_centrality",
    "within_module_degree_zscore",
    "participation_coefficient",
    "cross_community_bridge",
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_typed_graph(path):
    """Project typed parallel edges to a weighted simple undirected graph."""
    graph = nx.Graph()
    typed_edges = 0
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            source = str(row["source_id"])
            target = str(row["target_id"])
            if not source or not target or source == target:
                continue
            typed_edges += 1
            if graph.has_edge(source, target):
                graph[source][target]["weight"] += 1
            else:
                graph.add_edge(source, target, weight=1)
    return graph, typed_edges


def canonicalize_communities(communities):
    ordered = sorted(
        (sorted(str(node) for node in community) for community in communities),
        key=lambda members: (-len(members), members[0]),
    )
    return {node: community_id for community_id, members in enumerate(ordered) for node in members}


def detect_communities(graph, seed, resolution):
    communities = nx.community.louvain_communities(
        graph,
        weight="weight",
        resolution=resolution,
        seed=seed,
    )
    return canonicalize_communities(communities)


def _zscore(value, values):
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((item - mean) ** 2 for item in values) / len(values)
    return 0.0 if variance == 0 else (value - mean) / math.sqrt(variance)


def community_metrics(graph, membership, network_version, resolution):
    communities = {}
    for node, community_id in membership.items():
        communities.setdefault(community_id, []).append(node)

    internal_degrees = {}
    external_degrees = {}
    participation = {}
    for node in graph:
        weights_by_community = Counter()
        for neighbor, data in graph[node].items():
            weights_by_community[membership[neighbor]] += data.get("weight", 1)
        degree = sum(weights_by_community.values())
        internal = weights_by_community[membership[node]]
        internal_degrees[node] = internal
        external_degrees[node] = degree - internal
        participation[node] = (
            0.0
            if degree == 0
            else 1.0 - sum((weight / degree) ** 2 for weight in weights_by_community.values())
        )

    zscores = {}
    for nodes in communities.values():
        values = [internal_degrees[node] for node in nodes]
        for node in nodes:
            zscores[node] = _zscore(internal_degrees[node], values)

    member_rows = []
    for node in sorted(graph):
        community_id = membership[node]
        size = len(communities[community_id])
        internal = internal_degrees[node]
        member_rows.append(
            {
                "network_version": network_version,
                "resolution": resolution,
                "community_id": community_id,
                "node_id": node,
                "community_size": size,
                "degree": graph.degree(node, weight="weight"),
                "internal_degree": internal,
                "external_degree": external_degrees[node],
                "within_community_degree_centrality": internal / (size - 1) if size > 1 else 0.0,
                "within_module_degree_zscore": zscores[node],
                "participation_coefficient": participation[node],
                "cross_community_bridge": int(external_degrees[node] > 0),
            }
        )

    size_rows = []
    for community_id, nodes in sorted(communities.items()):
        subgraph = graph.subgraph(nodes)
        internal_weight = sum(data.get("weight", 1) for _, _, data in subgraph.edges(data=True))
        boundary_weight = sum(external_degrees[node] for node in nodes)
        size_rows.append(
            {
                "network_version": network_version,
                "resolution": resolution,
                "community_id": community_id,
                "community_size": len(nodes),
                "internal_typed_edge_weight": internal_weight,
                "cross_community_typed_edge_weight": boundary_weight,
            }
        )

    bridge_rows = []
    for source, target, data in graph.edges(data=True):
        source_community = membership[source]
        target_community = membership[target]
        if source_community != target_community:
            bridge_rows.append(
                {
                    "network_version": network_version,
                    "resolution": resolution,
                    "source_id": min(source, target),
                    "target_id": max(source, target),
                    "source_community_id": membership[min(source, target)],
                    "target_community_id": membership[max(source, target)],
                    "typed_edge_weight": data.get("weight", 1),
                }
            )
    bridge_rows.sort(key=lambda row: (row["source_id"], row["target_id"]))
    return member_rows, size_rows, bridge_rows


def assoc_exact_year_distribution(path):
    exact_edges = 0
    total_edges = 0
    years = Counter()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            total_edges += 1
            if row.get("year_precision") != "exact":
                continue
            exact_edges += 1
            for value in set(filter(None, row.get("year_values", "").split(";"))):
                years[int(value)] += 1
    rows = [{"year": year, "exact_edge_count": count} for year, count in sorted(years.items())]
    return rows, {
        "total_edges": total_edges,
        "exact_edges": exact_edges,
        "missing_or_non_exact_edges": total_edges - exact_edges,
        "missing_or_non_exact_share": (total_edges - exact_edges) / total_edges,
        "counting_rule": "An exact edge is counted once for each distinct year in year_values.",
    }


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run(seed=DEFAULT_SEED, resolutions=DEFAULT_RESOLUTIONS, network_dir=NETWORK_DIR, output_dir=OUTPUT_DIR):
    input_manifest = network_dir / "manifest.json"
    input_manifest_hash = sha256(input_manifest)
    manifest = {
        "schema_version": "community-analysis-v1",
        "command": "python3 python/compute_communities.py",
        "algorithm": "networkx.algorithms.community.louvain_communities",
        "networkx_version": nx.__version__,
        "seed": seed,
        "resolutions": list(resolutions),
        "input_manifest_sha256": input_manifest_hash,
        "network_versions": {},
        "temporal": {},
        "spatial": {
            "kin_edge_geography": "not_run_no_edge_geography",
            "assoc_edge_geography": "not_run_coverage_0.43_percent",
            "person_geography": "not_run_cost_deferred",
        },
        "limitations": [
            "Communities are structural algorithm outputs and are not named as historical factions.",
            "Typed parallel relation classes are projected to endpoint pairs and counted as integer edge weights.",
            "Louvain is heuristic; the fixed seed and alternate resolution support reproducibility and sensitivity comparison, not historical validation.",
            "KIN temporal analysis is not run because KIN_DATA has no edge-year field.",
            "ASSOC temporal output is descriptive only and excludes unknown/non-exact years; no dynamic network is constructed.",
            "Edge-level spatial analysis is not run; person-level spatial description is deferred.",
        ],
        "output_files": {},
    }
    output_dir.mkdir(parents=True, exist_ok=True)

    for version in NETWORK_VERSIONS:
        input_path = network_dir / f"{version}.csv"
        graph, typed_edges = read_typed_graph(input_path)
        version_summary = {
            "input_sha256": sha256(input_path),
            "nodes": graph.number_of_nodes(),
            "projected_endpoint_edges": graph.number_of_edges(),
            "typed_edges": typed_edges,
            "runs": {},
        }
        for resolution in resolutions:
            membership = detect_communities(graph, seed, resolution)
            members, sizes, bridges = community_metrics(graph, membership, version, resolution)
            label = str(resolution).replace(".", "p")
            files = {
                f"{version}_resolution_{label}_members.csv": (members, MEMBER_FIELDS),
                f"{version}_resolution_{label}_sizes.csv": (
                    sizes,
                    ("network_version", "resolution", "community_id", "community_size", "internal_typed_edge_weight", "cross_community_typed_edge_weight"),
                ),
                f"{version}_resolution_{label}_bridges.csv": (
                    bridges,
                    ("network_version", "resolution", "source_id", "target_id", "source_community_id", "target_community_id", "typed_edge_weight"),
                ),
            }
            for filename, (rows, fields) in files.items():
                output_path = output_dir / filename
                write_csv(output_path, rows, fields)
                manifest["output_files"][filename] = {"rows": len(rows), "sha256": sha256(output_path)}
            version_summary["runs"][str(resolution)] = {
                "communities": len(sizes),
                "largest_community": max(row["community_size"] for row in sizes),
                "bridge_endpoint_edges": len(bridges),
                "modularity": nx.community.modularity(
                    graph,
                    [{node for node, community_id in membership.items() if community_id == cid} for cid in sorted(set(membership.values()))],
                    weight="weight",
                    resolution=resolution,
                ),
            }
        manifest["network_versions"][version] = version_summary

    temporal_rows, temporal_summary = assoc_exact_year_distribution(network_dir / "assoc_typed_undirected.csv")
    temporal_path = output_dir / "assoc_exact_year_distribution.csv"
    write_csv(temporal_path, temporal_rows, ("year", "exact_edge_count"))
    manifest["output_files"][temporal_path.name] = {"rows": len(temporal_rows), "sha256": sha256(temporal_path)}
    manifest["temporal"] = {
        "kin": "not_run_structural_year_missingness",
        "assoc": temporal_summary,
        "interpretation": "descriptive_exact_year_edges_only_no_dynamic_network",
    }
    manifest_path = output_dir / "community_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--resolutions", type=float, nargs="+", default=DEFAULT_RESOLUTIONS)
    args = parser.parse_args()
    manifest = run(seed=args.seed, resolutions=tuple(args.resolutions))
    for version, summary in manifest["network_versions"].items():
        runs = ", ".join(f"r={key}: {value['communities']} communities" for key, value in summary["runs"].items())
        print(f"{version}: {summary['nodes']} nodes, {summary['typed_edges']} typed edges; {runs}")
    assoc = manifest["temporal"]["assoc"]
    print(f"ASSOC exact-year edges: {assoc['exact_edges']}/{assoc['total_edges']}; missing/non-exact {assoc['missing_or_non_exact_share']:.1%}")


if __name__ == "__main__":
    main()
