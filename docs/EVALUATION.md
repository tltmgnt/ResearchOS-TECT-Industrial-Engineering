# Experimental evaluation protocol

The industrial example is a deterministic integration fixture, not an experimental comparison. No human subjects or foundation models have been evaluated, and no performance improvement is claimed.

## Matched four-condition study

Use the same authorized task set for A: human researchers with conventional tools; B: a single foundation model with standard prompting; C: an unstructured multi-agent workflow; D: ResearchOS with TECT gates. Preserve model versions, prompts, compute budgets, task order randomization, reviewer identities, and dataset versions. Freeze the controller policy before holdout evaluation. Independent adjudicators establish materially correct/incorrect labels without seeing condition labels.

Use paired tasks, record abstentions and missing results, report denominators and uncertainty intervals, and stratify by task difficulty and criticality. Count accepted incorrect claims as false acceptance, not merely failures the adversary found. Measure detection recall only against independently established failures. Measure audit reconstruction time with blinded reviewers and identical questions. Pre-register the analysis and select thresholds after pilot characterization.

## Result rows

`python -m examples.score_runs examples/evaluation_fixture.json` checks and aggregates a small **synthetic scoring fixture**. To evaluate actual runs, supply rows with:

- `condition`: A, B, C, or D
- `task_id`: unique per condition
- `seconds`, `reviewer_hours`: finite nonnegative costs (seconds must be positive)
- `correct`, `accepted`, `reproduced`, `failure_present`, `failure_detected`: booleans

The utility reports accepted and correct throughput, accepted false-claim rate, reproduction among accepted results, detection recall, and reviewer burden. It does not measure audit reconstruction time, empirical stability, statistical significance, or unseen-attack performance; collect these separately. Do not equate a rejected unsupported claim with a verified false claim.
