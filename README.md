# ResearchOS TECT — Industrial Engineering

An experimental epistemic control and assurance infrastructure for AI-generated knowledge, based on **Topological Epistemic Control Theory (TECT)**.

**AI generation ≠ knowledge acceptance.** ResearchOS registers candidate claims, tracks evidence and dependencies, gates promotions, records challenges, and exports an auditable assurance record.

This is a runnable Phase I reference prototype derived from the September 2026 conceptual white paper supplied by the project author. It is not a certified assurance system, a completed research program, or evidence of DARPA endorsement. All demonstration data is synthetic.

## Run locally

Python 3.11+; no runtime packages, API keys, model providers, or external services required.

```bash
# From the repository root
python -m unittest discover -s tests -v
python -m examples.industrial_engineering

# Generate and keep a local admin credential for this terminal session
export RESEARCHOS_ADMIN_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python -m researchos.server
```

Open **http://127.0.0.1:8080**. Paste the value of `RESEARCHOS_ADMIN_TOKEN` into the access-token field and connect. The synthetic demo has already populated `researchos.db`. Select its claim to inspect checks, open a challenge, and export assurance JSON. Tokens stay in browser memory and are not persisted in browser storage.

For separate roles, also set distinct `RESEARCHOS_RESEARCHER_TOKEN` and `RESEARCHOS_REVIEWER_TOKEN` values. Researchers register claims and evidence; reviewers record checks, resolve challenges, and approve higher states; only admins can assure critical claims. The API derives roles from server configuration and ignores client-supplied role fields. The default admin token represents a local operator, not a multi-user identity provider.

Optional package installation: `python -m pip install .`; then run `researchos`. Persist and back up the SQLite database. The server binds exclusively to loopback. Production identity, TLS, tenant isolation, signed external ledger anchoring, database migration, and operational hardening are future work.

## Implemented

- SQLite-backed claim graph with stable IDs, versions, provenance, evidence, dependencies, and challenges.
- Explicit sequential lifecycle: Generated → Unverified → Supported → Adversarial Test → Reproduced → Validated → Stable → Assured.
- PASS / FAIL / UNCERTAIN records, role gates, critical-claim approval, and logged rejection reasons.
- Conservative evidence clustering by declared common origin; duplicated sources count once.
- Three executable structural screens: unresolved contradictions, source-group collapse, and invalid dependency assumptions.
- Fresh-check requirements following material changes; transitive downstream contestation.
- Transactional hash-chained decision ledger and JSON assurance exports containing the full verification chain.
- Responsive operator interface for registration, evidence, checks, dependencies, challenges, transitions, and exports.
- Synthetic line-capacity demonstration and an experiment-result scoring utility.
- Automated controller and HTTP integration tests plus GitHub Actions across Python 3.11–3.13.

## Research boundaries

Checks are recorded reviewer attestations. Built-in attacks inspect graph structure, not the truth of natural-language claims. Evidence independence is declared; the prototype cannot infer hidden source correlation. Stable means the configured checks passed for the current version, not formal ε-stability. No theorem, calibrated confidence score, ORI, convergence guarantee, 5× throughput gain, or 95% reproduction performance is claimed.

The prototype implements a deliberately narrow dependency graph. General typed reasoning edges, automated claim extraction, LLM generation, scientific simulation adapters, calibrated confidence, empirical stability distance, general governance policies, and multi-domain validation remain research work. High-level Python APIs are trusted internal interfaces; the HTTP boundary enforces configured roles.

## Documentation

- [TECT specification and design choices](docs/TECT.md)
- [API reference](docs/API.md)
- [Machine-readable assurance schema](schemas/assurance.schema.json)
- [Experimental protocol and scoring](docs/EVALUATION.md)
- [Phase I milestones and research roadmap](docs/ROADMAP.md)
- [Security and operational limits](SECURITY.md)

Apache-2.0; see [LICENSE](LICENSE).
