# Deduplicated Pi-hole blocklist for network-wide DNS filtering

[![Update blocklist](https://github.com/iamwaqargulzar/pihole-curated-blocklist/actions/workflows/update.yml/badge.svg)](https://github.com/iamwaqargulzar/pihole-curated-blocklist/actions/workflows/update.yml)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![Pi-hole: v6](https://img.shields.io/badge/Pi--hole-v6-96060c.svg)](https://pi-hole.net/)

This repository produces one Pi-hole v6 blocklist from six maintained DNS-filter sources. It normalizes hosts and Adblock Plus rules, removes exact duplicates and redundant subdomains, applies upstream exceptions before publishing, validates essential domains, and publishes build statistics. The result is designed for a home router where broad coverage matters but maintenance must remain predictable.

**Initial measured build (11 September 2026):** 490,378 block rules from 734,206 source rules. It removed 193,304 exact duplicates, 50,502 redundant descendants, and 22 block/allow conflicts. Counts change as upstream lists change; [the generated statistics](dist/stats.json) are authoritative.

## Use it with Pi-hole

Add this URL as a single subscribed list:

```text
https://raw.githubusercontent.com/iamwaqargulzar/pihole-curated-blocklist/main/dist/blocklist.txt
```

Then update Gravity:

```sh
pihole -g
```

Pi-hole refreshes Gravity automatically each week. This repository rebuilds daily, so the next normal Pi-hole refresh will pick up the latest successful release.

## What is included?

| Source | Variant | Main contribution |
|---|---|---|
| [HaGeZi DNS Blocklists](https://github.com/hagezi/dns-blocklists) | Multi PRO mini | Ads, tracking, telemetry and general abuse, size-optimized |
| [HaGeZi DNS Blocklists](https://github.com/hagezi/dns-blocklists) | TIF mini | Malware, phishing, scams and threat intelligence |
| [HaGeZi DNS Blocklists](https://github.com/hagezi/dns-blocklists) | DoH only | Known encrypted-DNS endpoints that can bypass local DNS policy |
| [oisd](https://oisd.nl/) | big | Broad ads, tracking and threat coverage with a functionality-first policy |
| [AdGuard DNS filter](https://github.com/AdguardTeam/AdGuardSDNSFilter) | default | DNS-specific advertising and tracking rules used by AdGuard services |
| [StevenBlack hosts](https://github.com/StevenBlack/hosts) | unified | Mature hosts-file aggregation from multiple curated projects |

Adult-content, gambling, piracy and blanket social-media lists are intentionally excluded. Those are household policy choices, not baseline ad blocking or network security.

Read [how the sources were evaluated](docs/source-evaluation.md) and [how the builder handles rules](docs/methodology.md).

## How deduplication works

The builder performs two levels of deduplication:

1. **Exact deduplication.** Equivalent domains from every source become one canonical lowercase ASCII domain.
2. **Semantic deduplication.** If `example.com` is wildcard-blocked, rules for `ads.example.com` and `track.ads.example.com` are redundant and removed.

Every emitted rule uses Pi-hole-compatible ABP syntax: `||example.com^`. Upstream `@@||example.com^` exceptions take priority during compilation: conflicting block rules are removed rather than emitting exception lines that Pi-hole Gravity does not import. The resulting format blocks both the named domain and its subdomains without expanding millions of predictable subdomain entries.

## Build safeguards

A scheduled build is rejected when:

- a source is unreachable or unexpectedly small;
- the final list falls outside the configured 200,000–1,000,000 rule range;
- an essential domain such as `github.com`, `google.com`, or `microsoft.com` would be blocked without an exception;
- unit tests fail.

The last good file remains available when a build fails. Each successful build includes [source counts and hashes](dist/stats.json) plus a [SHA-256 checksum](dist/blocklist.txt.sha256).

## Limitations

DNS filtering blocks hostnames, not page elements or network traffic in general. It cannot reliably remove YouTube video ads or ads served from the same hostname as wanted content. The DoH rules reduce common encrypted-DNS bypasses, but a new DoH endpoint, VPN, proxy, direct IP connection, or IPv6 path may still bypass a DNS-only rule.

Because this list deliberately combines broad sources, its false-positive risk is higher than using only HaGeZi Pro mini or oisd small. If an app or site stops working, check Pi-hole’s query log before allowing anything. See [reporting a false positive](CONTRIBUTING.md#report-a-false-positive).

## Frequently asked questions

### Is this a replacement for adding every popular list separately?

Yes. Subscribing to this generated feed and all of its upstream feeds wastes download, parsing and database work. Use this feed alone if you want this exact combination.

### Does a larger blocklist make DNS slower?

Ordinary lookups remain fast because Pi-hole keeps the compiled rules in memory. Larger lists mainly increase Gravity build time, memory use and the chance of false positives. That is why this project publishes one pre-deduplicated feed and enforces a maximum size.

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
(cd dist && sha256sum -c blocklist.txt.sha256)
```

Source URLs and minimum-size checks live in [sources.json](sources.json). Verified exceptions live in [allowlist.txt](allowlist.txt).

## Project status

This is an independent personal project, not an official Pi-hole, HaGeZi, oisd, AdGuard, or StevenBlack release. The first published build was produced and tested on 11 September 2026 for Pi-hole FTL 6.7 running through Entware on an ASUS RT-AX88U.

## License and attribution

The builder and generated compilation are available under GPL-3.0. Upstream data remains subject to its own copyright and license terms. HaGeZi, oisd, and AdGuard publish under GPL-3.0; StevenBlack uses MIT and preserves additional source attribution in its repository. See [LICENSE](LICENSE), [sources.json](sources.json), and the linked upstream projects before redistributing the data.
