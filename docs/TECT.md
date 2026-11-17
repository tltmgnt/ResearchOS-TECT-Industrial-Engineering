# TECT v0.1 reference semantics

Source: project-author-supplied “ResearchOS: Topological Epistemic Control Theory — DARPA-style technical white paper”, conceptual draft dated September 2026. This document maps that concept to an executable, restricted prototype. External solicitation, program, and legislative statements in the concept are not relied on by the software or independently verified here.

## Representation

The conceptual epistemic state is `(K, R, E, S, P, Γ)`: claims, relationships, evidence, status, provenance, and governance. Each claim has a UUID, monotonically increasing content version, statement, origin text, criticality, state, evidence, dependency IDs, challenges, checks, creation/update timestamps, and historical last-validation timestamp. The SQL transaction is the unit of persistence. A process-wide reentrant lock serializes operations in the reference server. Use one server process per database.

Dependency edges form a directed acyclic graph. Contradictions are challenge records attached to claims. General support/qualifies/reproduces edges are deferred. Claims are immutable in statement and provenance; a changed assertion is registered as a new claim.

## Evidence

Evidence retains source, common-origin group, method, observed result, timestamp, actor and finite unit-interval quality, reliability, and declared independence scores. Correlated copies in the same group contribute their maximum product, not a sum.

`density(k) = sum_group(max(quality × reliability × independence)) / (1 + dependency_count)`

This conservative grouped variant of the draft's validation-density expression is a research coverage indicator. It is not a confidence probability. Preliminary support requires two groups with positive contributions; the threshold is illustrative, not empirically calibrated. Users can still mislabel correlated sources as separate groups.

The prototype potential is only `unsupported_indicator + open_challenges + missing_provenance_indicator`. It is a diagnostic subset of the draft's potential, not an implemented convergence proof or a monotone optimization objective. Confidence calibration and formal epistemic distance remain open.

## Transition policy: tect-prototype-1

| Requested state | Additional predicate |
| --- | --- |
| Unverified | Generated claim registration, or a resolved contested claim |
| Supported | Two positive evidence origin groups |
| Adversarial Test | Sequential promotion with evidence prerequisites |
| Reproduced | All three adversarial screens PASS; reproduction PASS with a source group different from the support groups |
| Validated | Validation PASS; every declared dependency at least Validated; reviewer/admin |
| Stable | Same current-version checks; reviewer/admin; scope restricted to the recorded attack family |
| Assured | All prior gates; reviewer/admin; admin for critical claims |

All promotions must be sequential; any unresolved challenge or latest FAIL/UNCERTAIN check blocks promotion. Check precedence is latest per `(kind, attack)` on the current claim version. Earlier failures remain in the ledger after a subsequent passing rerun. The server never substitutes raw model confidence for required gates.

Evidence, dependency, challenge, and resolution mutations increment the content version, thereby staling prior checks. Material changes demote the claim to Unverified (or retain Contested) and transitively contest every dependent, incrementing dependent versions. A FAIL or UNCERTAIN check contests the subject and its transitive dependents. Contested claims can return to Unverified only after open challenges are resolved and blocking latest checks are rerun successfully. Positive state promotions do not mutate the content version.

Transitions are evaluated against the fixed versioned policy. Accepted and rejected transition events retain source state, destination, role, policy, content version, and reasons. Within this restricted policy, each accepted promotion satisfies the coded predicates at transaction time. This does not prove arbitrary real-world safety, confidentiality, or mission invariants.

## Assurance and ledger

The export contains the claim, metrics, policy, limitations, and complete local event chain. Each event's SHA-256 includes its canonical JSON and the prior event hash. This detects edits relative to a trusted chain head; a database owner can rewrite the chain or truncate it. No digital signature, remote witness, or immutable storage is implemented. Exports include the complete local ledger, so deployments must not mix audiences or restricted evidence.

## Mathematical limits

The paper's finite-state strict-descent argument requires a lower-bounded potential and an actual decrease on every non-stable accepted step. This prototype neither establishes those assumptions nor enforces potential descent. On a compact continuous state space, strict descent alone does not imply finite arrival in a stable region; a uniform decrease or suitable additional convergence assumptions are needed. The proposed margin-resilience statement likewise requires a defined metric, acceptance region, and perturbation bounds. These remain research obligations.

Stability can surround a false belief. Passing the prototype's structural screens does not demonstrate semantic correctness, unseen-attack robustness, or statistical improvements over baselines.
