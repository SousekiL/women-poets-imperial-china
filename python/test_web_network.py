import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_web_network import build


class WebNetworkBuildTest(unittest.TestCase):
    def test_counts_shards_and_schema_match_sources(self):
        source = Path(__file__).resolve().parents[1] / "data" / "derived" / "network"
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            manifest = build(source, out)
            expected = {}
            for key, name in {
                "people": "network_nodes.csv",
                "works": "work_nodes.csv",
                "direct": "direct_edges.csv",
                "work_edges": "work_person_edges.csv",
            }.items():
                with (source / name).open(encoding="utf-8-sig", newline="") as handle:
                    expected[key] = sum(1 for _ in csv.DictReader(handle))
            for key, value in expected.items():
                self.assertEqual(manifest["counts"][key], value)
            core = json.loads((out / "core.json").read_text(encoding="utf-8"))
            self.assertEqual(core["schema"], "web-network-v1")
            self.assertEqual(len(core["people"]), expected["people"])
            self.assertEqual(len(core["direct"]), expected["direct"])
            self.assertEqual(len(core["works"]), expected["works"])
            self.assertEqual(core["people_fields"][0], "id")
            self.assertEqual(core["direct_fields"][1:3], ["a", "b"])
            work_index = {item[0]: item for item in core["works"]}
            title_index = core["work_fields"].index("t")
            self.assertEqual(work_index["184"][title_index], "作品名不详一")
            self.assertEqual(work_index["426"][title_index], "作品名不详十")
            self.assertEqual(sum(item["edges"] for item in manifest["works"].values()), expected["work_edges"])
            for work_id, item in manifest["works"].items():
                shard = json.loads((out / item["file"]).read_text(encoding="utf-8"))
                self.assertEqual(shard["work"], work_id)
                self.assertEqual(len(shard["edges"]), item["edges"])


if __name__ == "__main__":
    unittest.main()
