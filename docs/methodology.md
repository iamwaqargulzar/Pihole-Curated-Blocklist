# Build methodology

Last reviewed: 11 September 2026

## Purpose

The builder converts several DNS blocklist formats into one deterministic Pi-hole v6 subscription. Its goal is to reduce redundant storage and parsing while retaining the union of supported upstream domain rules and using upstream exceptions as a safety layer.

## Processing pipeline

1. Download every source over HTTPS with retries and a fixed user agent.
2. Reject an empty response, a non-200 response, or a source below its expected minimum rule count.
3. Parse basic Adblock Plus domain rules, ABP exceptions, hosts-file entries and plain domains.
4. Normalize domains to lowercase IDNA ASCII and reject IP addresses, malformed names, comments, cosmetic filters and unsupported regular expressions.
5. Merge all blocking domains and exceptions into separate sets.
6. Remove exact duplicates across sources.
7. Apply exceptions before parent compression. Remove both block rules covered by an exception and broader parent rules that would otherwise cover the exception.
8. Remove a descendant block rule when a remaining parent rule already covers it.
9. Check essential public domains and enforce a bounded final rule count.
10. Sort the result, write ABP rules, and publish source hashes and build statistics.

## Semantic deduplication example

These three input rules have the same effective outcome when emitted as wildcard DNS rules:

```text
example.com
ads.example.com
pixel.ads.example.com
```

The output retains only:

```text
||example.com^
```

This transformation is more useful than line-level deduplication because Pi-hole v6 interprets the rule as the domain and all of its subdomains.

## Exception policy

All upstream ABP exceptions are merged. A local entry in `allowlist.txt` has the same effect. An exception for `example.com` covers that domain and its descendants, so any block rule completely covered by the exception is omitted from the generated file. Exceptions are applied while building; they are not emitted because Pi-hole Gravity treats subscribed `@@` lines as invalid entries.

This is intentionally conservative. A source that explicitly protects a domain from breakage can override a block supplied by another source. If a narrow exception conflicts with a broader parent block, the parent is removed while separately listed sibling or child blocks remain. This lowers false-positive risk, although it can also reduce blocking in a genuine disagreement between maintainers.

## What the parser does not import

The output excludes cosmetic rules, URL-path rules, scriptlets, content modifiers, arbitrary regular expressions, IP-only rules and application-specific syntax. A DNS resolver cannot apply browser page-element rules, and silently copying unsupported syntax would create a misleading rule count.

## Reproducibility

`dist/stats.json` records the build time, source URLs, downloaded byte counts, accepted rules, ignored lines and SHA-256 hash of each downloaded source. Upstream lists are rolling releases, so rebuilding an older commit may retrieve newer input unless the recorded source hash is reproduced from an archive.

The generated file is deterministic for identical source payloads and `allowlist.txt`: domains are normalized and sorted, and no random state is used. The timestamp is the only metadata value that changes independently of the rules.

## Operational trade-offs

Pre-deduplication reduces the file Pi-hole downloads and compiles, but it does not make a broad list equivalent to a narrow one. More unique rules still consume more memory and create more opportunities for false positives. The build’s upper bound is a failure guard, not a claim that every list below one million rules is appropriate for every device.
