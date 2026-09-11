# Security policy

## Supported version

Only the current `main` branch and latest generated list are supported.

## Reporting a vulnerability

Use a private GitHub security advisory for vulnerabilities in the builder or workflow. Do not open a public issue containing credentials, private DNS logs, router addresses, or another person’s browsing data.

False positives, missed malicious domains and ordinary source failures are data-quality issues rather than software vulnerabilities; use the relevant issue form.

## Supply-chain model

The build downloads rolling upstream lists over HTTPS and records a SHA-256 hash for each payload. Hashes provide traceability, not publisher authentication. Minimum-size checks, critical-domain checks, unit tests, bounded output size and Git history reduce accidental bad releases but cannot prove that every upstream rule is safe.
