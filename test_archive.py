import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = str(Path(folder.name) / "test.sqlite")
        self.cli("demo")

    def cli(self, *args, status=0):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("archive.py")), "--db", self.db, *args],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, status, result.stderr)
        return result.stdout

    def test_lookup_uses_only_past_observations(self):
        self.assertIn("30 days", self.cli("lookup", "demo-returns", "--at", "2026-11-09T13:59:59Z"))
        self.assertIn("14 days", self.cli("lookup", "demo-returns", "--at", "2026-11-09T14:00:00Z"))

    def test_missing_history(self):
        self.assertIn("No capture", self.cli("lookup", "demo-returns", "--at", "2020-01-01T00:00Z", status=1))

    def test_demo_is_repeatable_and_diff_is_chronological(self):
        self.cli("demo")
        diff = self.cli("diff", "demo-returns", "--at", "2026-11-10T00:00Z")
        self.assertIn("-Fictional example. You can return an item within 30 days of delivery.", diff)
        self.assertIn("+Fictional example. You can return an item within 14 days of delivery.", diff)

    def test_capture_keeps_original_if_timestamp_conflicts(self):
        file = Path(self.db).with_suffix(".txt")
        file.write_text("Original clause", encoding="utf-8")
        args = ["capture", "clause", str(file), "--url", "https://example.org/policy",
                "--at", "2026-11-04T17:00:00+07:00"]
        self.cli(*args)
        file.write_text("Updated clause", encoding="utf-8")
        self.cli(*args, status=2)
        self.assertIn("Original clause", self.cli("lookup", "clause", "--at", args[-1]))

    def test_cancellation_history_is_separate(self):
        text = self.cli("lookup", "demo-cancellation", "--at", "2026-11-10T00:00Z")
        self.assertIn("48 hours", text)
        self.assertNotIn("delivery", text)
