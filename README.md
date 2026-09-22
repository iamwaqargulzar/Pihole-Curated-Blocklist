# Deduplicated Pi-hole blocklist for network-wide DNS filtering

[![Update blocklist](https://github.com/iamwaqargulzar/pihole-curated-blocklist/actions/workflows/update.yml/badge.svg)](https://github.com/iamwaqargulzar/pihole-curated-blocklist/actions/workflows/update.yml)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![Pi-hole: v6](https://img.shields.io/badge/Pi--hole-v6-96060c.svg)](https://pi-hole.net/)

This repository combines 96 DNS-filter sources into one logical Pi-hole v6 dataset. It normalizes hosts and Adblock Plus rules, removes exact duplicates and redundant subdomains, applies upstream exceptions, and partitions the complete result into eight deterministic files that remain below GitHub's per-file limit.

The supplied Pi-hole regex feed is retained separately in [`unsupported-sources.txt`](unsupported-sources.txt), because regular expressions do not enumerate individual domains and cannot be safely converted into finite DNS rules.

**Initial measured build (11 September 2026):** 491,761 block rules from 734,270 source rules. It removed 193,320 exact duplicates, 49,068 redundant descendants, and 121 block/allow conflicts. Counts change as upstream lists change; [the generated statistics](dist/stats.json) are authoritative.

## Use it with Pi-hole

Add all eight URLs as subscribed lists:

```text
https://raw.githubusercontent.com/iamwaqargulzar/Pihole-Curated-Blocklist/main/dist/blocklist-01.txt
https://raw.githubusercontent.com/iamwaqargulzar/Pihole-Curated-Blocklist/main/dist/blocklist-02.txt
https://raw.githubusercontent.com/iamwaqargulzar/Pihole-Curated-Blocklist/main/dist/blocklist-03.txt
https://raw.githubusercontent.com/iamwaqargulzar/Pihole-Curated-Blocklist/main/dist/blocklist-04.txt
https://raw.githubusercontent.com/iamwaqargulzar/Pihole-Curated-Blocklist/main/dist/blocklist-05.txt
https://raw.githubusercontent.com/iamwaqargulzar/Pihole-Curated-Blocklist/main/dist/blocklist-06.txt
https://raw.githubusercontent.com/iamwaqargulzar/Pihole-Curated-Blocklist/main/dist/blocklist-07.txt
https://raw.githubusercontent.com/iamwaqargulzar/Pihole-Curated-Blocklist/main/dist/blocklist-08.txt
```

Then update Gravity:

```sh
pihole -g
```

Pi-hole refreshes Gravity automatically each week. All eight files are required; together they contain the complete deduplicated set. [`dist/stats.json`](dist/stats.json) and [`dist/checksums.sha256`](dist/checksums.sha256) describe each current part.

## What is included?

The build includes the six structured sources in [`sources.json`](sources.json) and all 90 deduplicated URLs in [`additional-sources.txt`](additional-sources.txt), including advertising, tracking, telemetry, malware, phishing, fraud, ransomware, Smart TV, mobile-device, adult-content and gambling feeds.

Read [how the sources were evaluated](docs/source-evaluation.md) and [how the builder handles rules](docs/methodology.md).

## How deduplication works

The builder performs two levels of deduplication:

1. **Exact deduplication.** Equivalent domains from every source become one canonical lowercase ASCII domain.
2. **Semantic deduplication.** If `example.com` is wildcard-blocked, rules for `ads.example.com` and `track.ads.example.com` are redundant and removed.

Every emitted rule uses Pi-hole-compatible ABP syntax: `||example.com^`. Upstream `@@||example.com^` exceptions take priority during compilation: conflicting block rules are removed rather than emitting exception lines that Pi-hole Gravity does not import. The resulting format blocks both the named domain and its subdomains without expanding millions of predictable subdomain entries.

## Build safeguards

A scheduled build is rejected when:

- a source is unreachable or unexpectedly small;
- the final list falls outside the configured 200,000–10,000,000 rule range;
- an essential domain such as `github.com`, `google.com`, or `microsoft.com` would be blocked without an exception;
- unit tests fail.

The last good files remain available when a build fails. Each successful build includes [source counts and hashes](dist/stats.json) plus [SHA-256 checksums](dist/checksums.sha256).

## Limitations

DNS filtering blocks hostnames, not page elements or network traffic in general. It cannot reliably remove YouTube video ads or ads served from the same hostname as wanted content. The DoH rules reduce common encrypted-DNS bypasses, but a new DoH endpoint, VPN, proxy, direct IP connection, or IPv6 path may still bypass a DNS-only rule.

Because this list deliberately combines broad sources, its false-positive risk is higher than using only HaGeZi Pro mini or oisd small. If an app or site stops working, check Pi-hole’s query log before allowing anything. See [reporting a false positive](CONTRIBUTING.md#report-a-false-positive).

## Frequently asked questions

### Is this a replacement for adding every popular list separately?

Yes. Subscribe to the eight generated parts, not to their upstream feeds. Pi-hole combines the parts into one Gravity database.

### Does a larger blocklist make DNS slower?

Ordinary lookups use Pi-hole's compiled database. Larger lists substantially increase Gravity build time, storage, memory use and false-positive risk; splitting only solves GitHub's file-size limit.

### Why include several lists with overlapping coverage?

Overlap is expected, but the sources use different inputs and curation policies. The builder removes redundant output while retaining domains unique to each source. The statistics make the cost and contribution visible instead of assuming that every extra source adds equal value.

### How often is the list updated?

GitHub Actions checks the sources once per day at 03:17 UTC. A commit is created only when the generated files change.

### Can this block every DNS bypass?

No. The DoH source blocks known endpoint hostnames. Enforcing network DNS also requires router firewall policy for ordinary DNS and DNS-over-TLS/QUIC, plus a considered IPv6 policy. VPNs and unknown endpoints require controls beyond a blocklist.

## Reproduce the build

Python 3.11 or later is recommended; there are no third-party packages.

```sh
python3 -m unittest discover -s tests -v
python3 build.py
(cd dist && sha256sum -c checksums.sha256)
```

Source URLs live in [sources.json](sources.json) and [additional-sources.txt](additional-sources.txt). Verified exceptions live in [allowlist.txt](allowlist.txt).

## Project status

This is an independent personal project, not an official Pi-hole, HaGeZi, oisd, AdGuard, or StevenBlack release. The first published build was produced and tested on 11 September 2026 for Pi-hole FTL 6.7 running through Entware on an ASUS RT-AX88U.

## License and attribution

The builder and generated compilation are available under GPL-3.0. Upstream data remains subject to its own copyright and license terms. HaGeZi, oisd, and AdGuard publish under GPL-3.0; StevenBlack uses MIT and preserves additional source attribution in its repository. See [LICENSE](LICENSE), [sources.json](sources.json), and the linked upstream projects before redistributing the data.
