import unittest

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


if __name__ == "__main__":
    unittest.main()
