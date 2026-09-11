# Pi-hole blocklist source evaluation for a home router

Last reviewed: 11 September 2026

## Recommendation

For a 1 GB ASUS RT-AX88U running Pi-hole FTL 6.7 through Entware, a prebuilt feed of roughly 500,000 wildcard rules is a practical upper-middle configuration: broad enough to combine advertising, tracking and threat intelligence, but far below multi-million-rule collections. The important controls are predictable updates, deduplication, source validation and a quick false-positive path—not the largest possible domain count.

This project combines HaGeZi Pro mini, HaGeZi TIF mini, HaGeZi DoH-only, oisd big, AdGuard DNS Filter, and StevenBlack hosts. They were selected for active maintenance, public provenance, Pi-hole-compatible data, distinct curation policies, and broad recognition in the DNS-filtering ecosystem.

## Measured comparison

The following counts were downloaded on 11 September 2026. Counts represent parseable blocking rules before cross-source deduplication, not a promise of stable future size.

| Source | Rules observed | Exact domains found only in this source | Decision |
|---|---:|---:|---|
| HaGeZi Pro mini | 50,212 | 19,267 | Include: balanced, size-optimized coverage |
| HaGeZi TIF mini | 176,800 | 90,654 | Include: threat intelligence companion |
| HaGeZi DoH only | 3,318 | 3,279 | Include: encrypted-DNS endpoint hostnames |
| oisd big | 246,701 | 96,323 | Include: broad, functionality-first policy |
| AdGuard DNS Filter | 177,211 block rules plus 176 exceptions | 113,750 | Include: widely deployed DNS filter |
| StevenBlack unified hosts | 79,964 | 53,310 | Include: independent hosts-file lineage |
| oisd small | 55,490 | Not measured | Exclude: subset of oisd big |
| 1Hosts Lite | about 202,970 lines | Not measured | Exclude from first release: another broad aggregator |

The six selected feeds contributed 734,206 raw block rules. Exact cross-source deduplication reduced that to 540,902 unique domains. Removing 50,502 child domains already covered by a blocked parent and resolving 22 allow conflicts produced 490,378 final block rules. “Only in this source” is an exact-domain comparison before parent compression; it shows that every selected feed added distinct data, but it does not prove every added rule is equally valuable. These are original measurements from this repository’s first build; current counts are always available in [`dist/stats.json`](../dist/stats.json).

## Why these sources

### HaGeZi

HaGeZi is the strongest fit for a router-conscious baseline. Its documentation calls Pro the general recommendation, says a main tier should be paired with TIF, and explicitly offers mini editions for limited hardware. It also warns against subscribing to multiple main tiers because they are nested. The current repository is highly active and had roughly 26,000 GitHub stars during this review. [HaGeZi FAQ](https://github.com/hagezi/dns-blocklists/blob/main/FAQ.md), [HaGeZi repository](https://github.com/hagezi/dns-blocklists)

Pro mini selects popular domains from the full Pro policy, while TIF mini adds phishing, malware, scam and related intelligence without using the multi-million-entry full TIF feed. The DoH-only list complements router DNS redirection by denying known encrypted-DNS hostnames; HaGeZi correctly notes that firewall rules for ports 53 and 853 are still required. [HaGeZi list documentation](https://github.com/hagezi/dns-blocklists/blob/main/README.md?plain=1)

### oisd

oisd big covers advertising, mobile-app ads, phishing, malware, spyware, ransomware, cryptojacking, and tracking where blocking is not considered necessary for functionality. It is updated at least daily, prunes dead domains every five days, and documents known breakage openly. oisd states that big already contains small, so both should never be subscribed together. [oisd Pi-hole setup](https://oisd.nl/setup/pihole), [oisd FAQ](https://oisd.nl/faq)

oisd is included because its functionality-first exclusion policy differs from the other aggregators. Its exceptions can prevent a domain another feed would block, which this project treats as a conservative safety signal.

### AdGuard DNS Filter

AdGuard’s DNS filter combines AdGuard Base, Tracking Protection, Mobile Ads, EasyList, EasyPrivacy, and regional inputs into DNS-level rules. It is the default filter used by AdGuard Home and public AdGuard DNS, making it one of the most widely deployed policy sets in this comparison. Its basic ABP syntax is directly relevant to Pi-hole v6. [AdGuard DNS Filter repository](https://github.com/AdguardTeam/AdGuardSDNSFilter)

The filter’s explicit exception rules are retained. Unsupported browser-only syntax is counted as ignored rather than presented as working DNS protection.

### StevenBlack hosts

StevenBlack’s project is a long-running merge of curated hosts sources with duplicates removed. It had roughly 31,000 GitHub stars and 4,500 commits during this review, making it the most visible GitHub project in the shortlist. The standard list contained 79,962 domains in its 9 September 2026 release. [StevenBlack hosts repository](https://github.com/StevenBlack/hosts)

Its coverage overlaps modern ABP lists, but its independent hosts-file lineage still contributes unique domains and a useful second curation path.

## Popular alternatives not included

### 1Hosts Lite

1Hosts Lite is a credible balanced list designed for general users and low false-positive rates. Its project had about 2,200 GitHub stars during this review and supports Pi-hole directly. It is a sensible alternative to this combined feed, especially for users who prefer one curator. It was excluded from the first combined release because another large all-purpose source added less value than its raw size suggested after the existing four coverage families. [1Hosts repository](https://github.com/badmojr/1Hosts)

### Block List Project

The Block List Project is useful when category control matters. It offers separate advertising, tracking, malware, phishing, ransomware, fraud, Smart TV and other lists; the project reports automated upstream monitoring, weekly dead-domain checks, and more than 151 tests. It had about 5,000 GitHub stars during this review. [Block List Project repository](https://github.com/blocklistproject/Lists)

Its granular categories are better added deliberately than swept into a general household list. TIF and oisd already provide broad threat coverage here, while categories such as gambling, piracy and social networks require an explicit household policy decision.

### Firebog

Firebog remains a well-known directory of third-party lists, especially its green “ticked” recommendations. It is a source catalog rather than one consistent policy. Importing every ticked feed increases the number of upstream failure points and makes a false positive harder to trace. It is most useful when an operator wants to choose individual specialists, not when the goal is a single reproducible feed. [Firebog](https://firebog.net/)

## Popularity is not quality

GitHub stars are a useful signal that maintainers receive scrutiny, but they are not usage counts, accuracy tests, or false-positive measurements. Projects hosted outside GitHub, such as oisd, cannot be compared fairly by stars. This evaluation therefore uses popularity only as one filter alongside update cadence, transparent methodology, supported syntax, licensing, and fit for router hardware.

## Why not merge everything?

Pi-hole Gravity already sorts subscribed domains, but its database keeps source relationships and every extra feed must still be downloaded and parsed. Pi-hole’s documentation describes Gravity as downloading each source, parsing it, merging it, removing comments, sorting uniquely and rebuilding the gravity table. Prebuilding one feed moves much of that work off the router and makes the exact compilation auditable. [Pi-hole Gravity command](https://docs.pi-hole.net/main/pihole-command/), [Pi-hole domain database](https://docs.pi-hole.net/database/domain-database/)

More importantly, list size has diminishing returns. The first six sources contained 734,206 parseable block rules but only 540,902 unique domains before parent-domain compression. Raw rule totals would have overstated distinct coverage by more than 193,000 entries.

## Known limits

No DNS blocklist can reliably remove ads delivered from the same hostname as requested content. oisd specifically notes that DNS blockers cannot block YouTube video ads. A browser content blocker is still needed for page elements and same-origin advertising. [oisd FAQ](https://oisd.nl/faq)

Likewise, a hostname list cannot guarantee DNS enforcement. Router rules must redirect ordinary DNS and block DNS-over-TLS/QUIC as appropriate; unknown DoH servers, VPNs, proxies, direct IP traffic and alternate IPv6 paths remain separate control problems.

## Review policy

Source inclusion should be reconsidered when a feed becomes stale, repeatedly fails, changes license, produces abnormal size changes, creates disproportionate false positives, or becomes fully redundant. A source should not be added solely because it is popular or because it makes the final domain count larger.
