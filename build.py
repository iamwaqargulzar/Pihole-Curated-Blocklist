#!/usr/bin/env python3
"""Build a conservative, semantically deduplicated Pi-hole v6 blocklist."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import ipaddress
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DOMAIN_RE = re.compile(
    r"^(?=.{1,253}\.?$)(?:[a-z0-9_](?:[a-z0-9_-]{0,61}[a-z0-9_])?\.)+"
    r"(?:[a-z0-9_](?:[a-z0-9_-]{0,61}[a-z0-9_])?)$"
)
ABP_RE = re.compile(
    r"^(?P<exception>@@)?\|\|(?:https?://)?"
    r"(?P<domain>[^/^$*|:]+)(?:[/:^$]|$)"
)
HOSTS_IPS = {"0.0.0.0", "127.0.0.1", "::", "::1"}
CRITICAL_DOMAINS = {
    "amazon.com",
    "apple.com",
    "cloudflare.com",
    "github.com",
    "google.com",
    "icloud.com",
    "microsoft.com",
    "mozilla.org",
    "openai.com",
    "reddit.com",
    "wikipedia.org",
}
MINIMUM_COMBINED_RULES = 200_000
MAXIMUM_COMBINED_RULES = 1_000_000


@dataclass
class Parsed:
    blocks: set[str]
    allows: set[str]
    rejected: int = 0


def normalize_domain(value: str) -> str | None:
    value = value.strip().lower().rstrip(".")
    if value.startswith("*."):
        value = value[2:]
    if not value or ":" in value or "/" in value:
        return None
    try:
        value = value.encode("idna").decode("ascii")
        ipaddress.ip_address(value)
        return None
    except UnicodeError:
        return None
    except ValueError:
        pass
    if value in {"localhost", "localhost.localdomain", "broadcasthost"}:
        return None
    return value if DOMAIN_RE.fullmatch(value) else None


def parse_content(content: str) -> Parsed:
    parsed = Parsed(set(), set())
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith(("!", "#", "[")):
            continue

        match = ABP_RE.match(line)
        if match:
            domain = normalize_domain(match.group("domain"))
            if domain:
                target = parsed.allows if match.group("exception") else parsed.blocks
                target.add(domain)
            else:
                parsed.rejected += 1
            continue

        fields = line.split()
        if len(fields) >= 2 and fields[0] in HOSTS_IPS:
            accepted = False
            for field in fields[1:]:
                domain = normalize_domain(field)
                if domain:
                    parsed.blocks.add(domain)
                    accepted = True
            if not accepted:
                parsed.rejected += 1
            continue

        if len(fields) == 1:
            domain = normalize_domain(fields[0])
            if domain:
                parsed.blocks.add(domain)
            else:
                parsed.rejected += 1
            continue

        parsed.rejected += 1
    return parsed


def fetch(url: str, attempts: int = 3) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "pihole-curated-blocklist/1.0 (+GitHub Actions)"},
    )
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                data = response.read()
                if not data:
                    raise RuntimeError("empty response")
                return data
        except (OSError, urllib.error.URLError, RuntimeError) as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    raise RuntimeError(f"failed to download {url}: {last_error}")


def is_covered(domain: str, selected: set[str]) -> bool:
    labels = domain.split(".")
    return any(".".join(labels[index:]) in selected for index in range(len(labels) - 1))


def domain_and_parents(domain: str) -> set[str]:
    labels = domain.split(".")
    return {".".join(labels[index:]) for index in range(len(labels) - 1)}


def collapse_descendants(domains: set[str]) -> tuple[set[str], int]:
    selected: set[str] = set()
    for domain in sorted(domains, key=lambda item: (item.count("."), len(item), item)):
        if not is_covered(domain, selected):
            selected.add(domain)
    return selected, len(domains) - len(selected)


def load_local_allowlist(path: Path) -> set[str]:
    if not path.exists():
        return set()
    result: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.partition("#")[0].strip()
        if line:
            domain = normalize_domain(line)
            if not domain:
                raise ValueError(f"invalid local allowlist entry: {line}")
            result.add(domain)
    return result


def canonical_source_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"invalid source URL: {url}")
    path = parsed.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, "")
    )


def load_sources(root: Path, include_additional: bool = False) -> list[dict[str, object]]:
    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    extra_path = root / "additional-sources.txt"
    if extra_path.exists():
        for raw in extra_path.read_text(encoding="utf-8").splitlines():
            url = raw.partition("#")[0].strip()
            if not url:
                continue
            parsed = urllib.parse.urlsplit(url)
            basename = Path(parsed.path.rstrip("/")).name or parsed.netloc
            extra = {
                "name": f"{parsed.netloc} — {basename}",
                "url": url,
                "homepage": f"{parsed.scheme}://{parsed.netloc}/",
                "license": "See upstream",
                "minimum_rules": 1,
            }
            if include_additional:
                sources.append(extra)
            else:
                # Validate the catalog against active sources without enabling it.
                sources.append({**extra, "catalog_only": True})

    seen: dict[str, str] = {}
    for source in sources:
        canonical = canonical_source_url(str(source["url"]))
        if canonical in seen:
            raise ValueError(
                f"duplicate source URL: {source['url']} duplicates {seen[canonical]}"
            )
        seen[canonical] = str(source["url"])
    return [source for source in sources if include_additional or not source.get("catalog_only")]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate without writing output")
    args = parser.parse_args()

    sources = load_sources(ROOT)
    all_blocks: set[str] = set()
    all_allows: set[str] = load_local_allowlist(ROOT / "allowlist.txt")
    block_frequency: Counter[str] = Counter()
    source_block_sets: list[set[str]] = []
    source_stats: list[dict[str, object]] = []

    for source in sources:
        payload = fetch(source["url"])
        parsed = parse_content(payload.decode("utf-8", errors="replace"))
        accepted = len(parsed.blocks) + len(parsed.allows)
        minimum = int(source["minimum_rules"])
        if accepted < minimum:
            raise RuntimeError(
                f"{source['name']} yielded {accepted:,} rules; expected at least {minimum:,}"
            )
        all_blocks.update(parsed.blocks)
        all_allows.update(parsed.allows)
        block_frequency.update(parsed.blocks)
        source_block_sets.append(parsed.blocks)
        source_stats.append(
            {
                "name": source["name"],
                "url": source["url"],
                "download_bytes": len(payload),
                "block_rules": len(parsed.blocks),
                "allow_rules": len(parsed.allows),
                "ignored_lines": parsed.rejected,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    raw_block_count = sum(int(item["block_rules"]) for item in source_stats)
    allows, descendant_allows_removed = collapse_descendants(all_allows)
    unique_before_collapse = len(all_blocks)
    allow_ancestors = set().union(*(domain_and_parents(domain) for domain in allows)) if allows else set()
    allow_conflicts_removed = {
        domain
        for domain in all_blocks
        if is_covered(domain, allows) or domain in allow_ancestors
    }
    all_blocks.difference_update(allow_conflicts_removed)
    blocks, descendant_blocks_removed = collapse_descendants(all_blocks)

    for domain in CRITICAL_DOMAINS:
        if is_covered(domain, blocks) and not is_covered(domain, allows):
            raise RuntimeError(f"critical domain would be blocked: {domain}")

    if not MINIMUM_COMBINED_RULES <= len(blocks) <= MAXIMUM_COMBINED_RULES:
        raise RuntimeError(
            f"combined rule count {len(blocks):,} is outside safety range "
            f"{MINIMUM_COMBINED_RULES:,}-{MAXIMUM_COMBINED_RULES:,}"
        )

    for item, source_blocks in zip(source_stats, source_block_sets):
        # Frequency data gives an order-independent exact contribution metric.
        item["rules_unique_to_this_source"] = sum(
            1 for domain in source_blocks if block_frequency[domain] == 1
        )

    snapshot_material = "\n".join(
        str(item["sha256"]) for item in source_stats
    ) + "\n" + hashlib.sha256((ROOT / "allowlist.txt").read_bytes()).hexdigest()
    source_snapshot = hashlib.sha256(snapshot_material.encode()).hexdigest()
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    previous_stats = ROOT / "dist" / "stats.json"
    if previous_stats.exists():
        try:
            previous = json.loads(previous_stats.read_text(encoding="utf-8"))
            if previous.get("source_snapshot_sha256") == source_snapshot:
                generated = str(previous["generated_at"])
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            pass
    stats = {
        "generated_at": generated,
        "source_snapshot_sha256": source_snapshot,
        "source_count": len(sources),
        "source_block_rules_total": raw_block_count,
        "unique_block_domains_before_semantic_deduplication": unique_before_collapse,
        "duplicate_block_rules_removed": raw_block_count - unique_before_collapse,
        "descendant_block_rules_removed": descendant_blocks_removed,
        "allow_conflicts_removed": len(allow_conflicts_removed),
        "final_block_rules": len(blocks),
        "final_allow_rules": len(allows),
        "sources": source_stats,
    }

    if args.check:
        print(json.dumps(stats, indent=2))
        return 0

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    output = [
        "[Adblock Plus]",
        "! Title: Waqar's curated Pi-hole blocklist",
        "! Description: Popular maintained sources, normalized and semantically deduplicated.",
        f"! Last modified: {generated}",
        f"! Block rules: {len(blocks)}",
        f"! Upstream exceptions applied during build: {len(allows)}",
        "! Homepage: https://github.com/iamwaqargulzar/pihole-curated-blocklist",
        "! License: GPL-3.0; upstream licenses and attribution are documented in README.md",
        "!",
    ]
    output.extend(f"||{domain}^" for domain in sorted(blocks))
    text = "\n".join(output) + "\n"
    target = dist / "blocklist.txt"
    target.write_text(text, encoding="utf-8", newline="\n")
    (dist / "blocklist.txt.sha256").write_text(
        f"{hashlib.sha256(text.encode()).hexdigest()}  blocklist.txt\n",
        encoding="ascii",
    )
    (dist / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
