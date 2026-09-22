# Contributing

Small, evidence-based changes are welcome. This repository is a personal Pi-hole feed, so the maintainer may decline categories or aggressive rules that do not fit a general household network.

## Report a false positive

Before opening an issue:

1. Confirm the failure disappears when Pi-hole blocking is disabled briefly.
2. Find the exact blocked hostname in Pi-hole’s query log.
3. Run `pihole -q -exact -adlist hostname.example` to identify the source.
4. Include the affected app or site, the hostname, approximate time, and the smallest reproducible symptom.

Do not post passwords, IP addresses, authentication tokens, full query logs, or private browsing history. A verified local exception can be added to `allowlist.txt`; source-specific errors should also be reported upstream.

## Report a missed domain

Provide the exact hostname, what unwanted behavior it serves, and evidence that blocking it does not break required content. Screenshots alone are rarely enough because DNS filtering acts on hostnames.

## Change the source set

A source proposal should document its maintainer, license, update cadence, supported syntax, approximate rule count, category scope, false-positive process, and unique contribution relative to the current feeds.

## Validate a change

```sh
python3 -m unittest discover -s tests -v
python3 build.py
(cd dist && sha256sum -c checksums.sha256)
```

Review the changes in `dist/stats.json`. Large count changes require an explanation.
