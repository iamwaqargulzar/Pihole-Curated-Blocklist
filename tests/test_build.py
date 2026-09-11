import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build
from build import collapse_descendants, parse_content


class BuildTests(unittest.TestCase):
    def test_parse_supported_formats(self):
        parsed = parse_content(
            """
            # hosts
            0.0.0.0 ads.example.com
            tracker.example.net
            ||malware.example.org^
            @@||safe.example.org^
            ||wild.example.com^$important
            /unsupported-regex/
            """
        )
        self.assertEqual(
            parsed.blocks,
            {
                "ads.example.com",
                "tracker.example.net",
                "malware.example.org",
                "wild.example.com",
            },
        )
        self.assertEqual(parsed.allows, {"safe.example.org"})

    def test_semantic_deduplication(self):
        collapsed, removed = collapse_descendants(
            {"example.com", "ads.example.com", "deep.ads.example.com", "other.net"}
        )
        self.assertEqual(collapsed, {"example.com", "other.net"})
        self.assertEqual(removed, 2)

    def test_generated_feed_applies_but_does_not_emit_exceptions(self):
        source = b"||ads.example.com^\n@@||safe.example.com^\n||safe.example.com^\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "sources.json").write_text(
                '[{"name":"fixture","url":"https://example.test/list",'
                '"homepage":"https://example.test","license":"GPL-3.0",'
                '"minimum_rules":1}]'
            )
            (root / "allowlist.txt").write_text("")
            with (
                patch.object(build, "ROOT", root),
                patch.object(build, "MINIMUM_COMBINED_RULES", 1),
                patch.object(build, "fetch", return_value=source),
                patch.object(build, "CRITICAL_DOMAINS", set()),
                patch("sys.argv", ["build.py"]),
            ):
                self.assertEqual(build.main(), 0)
            output = (root / "dist" / "blocklist.txt").read_text()
            self.assertIn("||ads.example.com^", output)
            self.assertNotIn("||safe.example.com^", output)
            self.assertNotIn("@@", output)


if __name__ == "__main__":
    unittest.main()
