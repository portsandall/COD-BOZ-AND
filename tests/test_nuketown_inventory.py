"""Self-contained DTRZ index tests; no licensed assets needed."""
import gzip
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "nuketown"))
from inventory import DTRZError, read_dtrz, main  # noqa: E402


def sample_dz() -> bytes:
    names = ["kino.group.bin", "ascension.group.bin"]
    payloads = [gzip.compress(b"KINO"), gzip.compress(b"ASCENSION")]
    header = b"DTRZ" + struct.pack("<HH", len(names), 1) + b"\0"
    header += b"".join(name.encode() + b"\0" for name in names)
    for i in range(len(names)):
        header += struct.pack("<HHH", 0, i, 0x100)
    header += struct.pack("<HH", 0, len(names))
    offset = len(header) + len(names) * 16
    for payload in payloads:
        header += struct.pack("<IIII", offset, len(payload), len(payload), 8)
        offset += len(payload)
    return header + b"".join(payloads)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "test.dz"

    def tearDown(self):
        self.temp.cleanup()

    def test_parses_dtrz_and_finds_map_group(self):
        self.path.write_bytes(sample_dz())
        info = read_dtrz(self.path)
        self.assertEqual(info["file_count"], 2)
        self.assertEqual(info["group_bin_count"], 2)
        self.assertEqual(info["map_candidates"]["kino"], ["kino.group.bin"])
        self.assertFalse(info["map_candidates"]["nuketown"])
        self.assertTrue(all(x["gzip_header"] for x in info["files"]))

    def test_rejects_not_dtrz(self):
        self.path.write_bytes(b"BO2Fastfile")
        with self.assertRaises(DTRZError):
            read_dtrz(self.path)

    def test_rejects_truncated_index(self):
        self.path.write_bytes(sample_dz()[:13])
        with self.assertRaises(DTRZError):
            read_dtrz(self.path)

    def test_writes_json(self):
        self.path.write_bytes(sample_dz())
        out = Path(self.temp.name) / "report.json"
        rc = main(["--archive", str(self.path), "--json-out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(out.exists())
        self.assertIn("kino.group.bin", out.read_text())


if __name__ == "__main__":
    unittest.main()
