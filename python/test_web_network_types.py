import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_web_network import build


class WebNetworkTypePayloadTest(unittest.TestCase):
    def test_manifest_contains_compact_type_payloads(self):
        source = Path(__file__).resolve().parents[1] / "data" / "derived" / "network"
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            manifest = build(source, out)
            self.assertIn("types", manifest)
            self.assertIn("彈詞", manifest["types"])
            entry = manifest["types"]["彈詞"]
            self.assertGreater(entry["works"], 0)
            self.assertGreater(entry["edges"], 0)
            payload = json.loads((out / entry["file"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "web-network-type-v1")
            self.assertEqual(payload["type"], "彈詞")
            self.assertEqual(len(payload["works"]), entry["works"])
            self.assertEqual(len(payload["edges"]), entry["edges"])
            self.assertTrue(all("n" in edge and edge["n"] >= 1 for edge in payload["edges"]))


if __name__ == "__main__":
    unittest.main()
