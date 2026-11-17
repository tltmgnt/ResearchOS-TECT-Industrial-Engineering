# Phase I implementation and research roadmap

| Milestone | Delivered reference capability | Remaining research exit criterion |
| --- | --- | --- |
| M1 Formal specification | Versioned executable policy and explicit semantics | Formal distance, calibration, complete governance model, proof obligations |
| M2 Epistemic graph | Persistent claims, evidence, provenance, dependencies, challenges | General typed graph, large-scale performance characterization |
| M3 Controller | Sequential gates, role predicates, rollback, decision ledger | Independent invariant verification and richer mission policies |
| M4 Adversarial engine | Three structural screening operators | Semantic adversaries, hidden perturbations, poisoning/shift experiments |
| M5 Benchmarks | Result schema, scoring utility, four-condition protocol | Collect matched human and model baseline runs with ground truth |
| M6 Pilot | Deterministic synthetic industrial line-capacity example | External reproduction on authorized industrial data |
| M7 Feasibility report | Automated implementation checks | Quantitative comparisons, uncertainty intervals, cost and human-review study |

Next integrations should preserve the separation of generation, representation, verification, control, and assurance. Model adapters may register candidates, but should not self-assign reviewer permissions or supply unverified PASS records as accepted knowledge. Domain adapters should execute reproducible tests and retain their artifacts. Continuous-assurance deployments need authenticated per-user identities, least-privilege data access, external ledger anchoring, migrations, backups, and operational monitoring.

Potential materials, cyber, mission-planning, and AI-assurance demonstrations are future adapters. The current pilot only addresses a synthetic industrial engineering capacity claim. The research program's performance targets are objectives, not delivered results.
