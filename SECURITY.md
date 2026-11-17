# Prototype security and trust boundaries

Run on a trusted workstation bound to loopback. All data is stored in one SQLite file, without encryption or tenant partitioning. Each configured token maps to a shared role identity. Any authenticated role can read the entire workspace and ledger, including exports. Do not load restricted or classified evidence, expose the server publicly, or treat this as mission deployment authorization.

The HTTP layer resolves server-side roles; internal Python calls are trusted. Researchers can attach evidence and open challenges. Reviewers can attest checks and resolve challenges; admins additionally approve critical assurance. These attestations require honest, competent human or adapter execution. The system does not verify external sources, executor independence, or check artifacts.

Requests use explicit Bearer credentials and no cookies. Tokens are held only in the page input; they are not placed in URLs or browser storage. UI records are rendered with textContent. Static routes use an exact allowlist and a same-origin content security policy. No tools execute user-supplied code or fetch arbitrary URLs.

The ledger is hash chained, not cryptographically signed or externally anchored. A database administrator can replace the chain or delete its suffix. Back up data and retain trusted chain heads outside the database if experimenting with tamper detection. This reference server is single-process and lacks production rate limits, identity federation, data policy enforcement, and database migration management.

Report issues through the repository's private security advisory facility when available. Avoid posting credentials or sensitive evidence in public issues.
