import csv
import tempfile
import unittest
from pathlib import Path

import networkx as nx

from compute_communities import (
    assoc_exact_year_distribution,
    community_metrics,
    detect_communities,
    read_typed_graph,
)


class CommunityAnalysisFixture(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.path = Path(self.tempdir.name) / "edges.csv"
        self.path.write_text(
            "source_id,target_id,relation_class,year_values,year_precision\n"
            "a,b,F,1000,exact\n"
            "a,b,S,1000,exact\n"
            "a,c,F,,none\n"
            "b,c,F,1001;1002,exact\n"
            "c,d,F,,none\n"
            "d,e,F,,none\n"
            "d,f,F,,none\n"
            "e,f,F,,none\n",
            encoding="utf-8",
        )

    def test_typed_projection_and_reproducible_membership(self):
        graph, typed_edges = read_typed_graph(self.path)
        self.assertEqual(typed_edges, 8)
        self.assertEqual(graph.number_of_edges(), 7)
        self.assertEqual(graph["a"]["b"]["weight"], 2)
        first = detect_communities(graph, seed=20260822, resolution=1.0)
        second = detect_communities(graph, seed=20260822, resolution=1.0)
        self.assertEqual(first, second)
        self.assertEqual(first["a"], first["b"])
        self.assertEqual(first["d"], first["e"])

    def test_participation_and_bridge_metrics(self):
        graph, _ = read_typed_graph(self.path)
        membership = {"a": 0, "b": 0, "c": 0, "d": 1, "e": 1, "f": 1}
        members, sizes, bridges = community_metrics(graph, membership, "fixture", 1.0)
        by_node = {row["node_id"]: row for row in members}
        self.assertEqual(len(sizes), 2)
        self.assertEqual(len(bridges), 1)
        self.assertEqual((bridges[0]["source_id"], bridges[0]["target_id"]), ("c", "d"))
        self.assertEqual(by_node["c"]["cross_community_bridge"], 1)
        self.assertGreater(by_node["c"]["participation_coefficient"], 0)
        self.assertEqual(by_node["a"]["external_degree"], 0)

    def test_exact_year_distribution_is_descriptive(self):
        rows, summary = assoc_exact_year_distribution(self.path)
        counts = {row["year"]: row["exact_edge_count"] for row in rows}
        self.assertEqual(summary["total_edges"], 8)
        self.assertEqual(summary["exact_edges"], 3)
        self.assertEqual(counts, {1000: 2, 1001: 1, 1002: 1})
        self.assertAlmostEqual(summary["missing_or_non_exact_share"], 5 / 8)

    def test_louvain_available_in_networkx(self):
        self.assertTrue(hasattr(nx.community, "louvain_communities"))


if __name__ == "__main__":
    unittest.main()
