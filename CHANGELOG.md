# Changelog

## 2026-09-22

- Activated 90 additional domain-compatible upstream feeds after removing three duplicate URLs.
- Expanded the combined set to more than 6.5 million semantically deduplicated rules.
- Published the result in eight stable SHA-256 partitions below GitHub's file-size limit.
- Added per-part checksums, sizes and rule counts to the generated metadata.
- Documented the supplied regex-only feed separately because it does not enumerate domains.

## 2026-09-11

- Published the first combined Pi-hole v6 feed.
- Added six maintained upstream sources.
- Added exact and parent-domain semantic deduplication.
- Preserved upstream ABP exceptions and added a local allowlist.
- Added source-size checks, essential-domain checks, output bounds, hashes and tests.
- Added daily automated builds and reproducible build documentation.
- Applied ABP exceptions during compilation without emitting unsupported `@@` subscription lines.
- Applied exceptions before parent-domain compression so a broad block cannot swallow a narrow exception.
