# Local HTTP API v0.1

Base URL `http://127.0.0.1:8080`. All `/api/` routes require `Authorization: Bearer <configured role token>`. Send JSON objects for POST requests. Public routes are `/`, `/app.js`, `/style.css`, and `/health`. No CORS access is enabled. Bodies are limited to 1 MB.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/claims` | Claim and metric list |
| POST | `/api/claims` | Register statement, provenance, optional boolean critical |
| GET | `/api/claims/{id}` | Claim detail |
| POST | `/api/claims/{id}/evidence` | Add source, source_group, method, result, quality, reliability, independence |
| POST | `/api/claims/{id}/dependency` | Add upstream claim_id; cycles prohibited |
| POST | `/api/claims/{id}/challenge` | Add attack and detail |
| POST | `/api/claims/{id}/resolve` | Reviewer/admin resolution: challenge_id, resolution |
| POST | `/api/claims/{id}/check` | Reviewer/admin record: kind, outcome, method, runner, source_group; attack required for adversarial |
| POST | `/api/claims/{id}/attacks` | Reviewer/admin runs all three structural screens; send `{}` |
| POST | `/api/claims/{id}/transition` | Request target state |
| GET | `/api/claims/{id}/assurance` | Complete JSON assurance package |
| GET | `/api/ledger` | Event chain and verification status |

Check kinds: `validation`, `reproduction`, `adversarial`. Outcomes: `PASS`, `FAIL`, `UNCERTAIN`. Attack names: `contradiction`, `assumption_violation`, `source_poisoning`.

HTTP statuses: 201 created, 200 success, 400 invalid input, 403 invalid credential or insufficient role, 404 missing claim/route, 409 blocked transition (includes reasons and current claim), 413 body limit. Blocked transition responses are normal auditable decisions, not internal failures.

Example registration:

```bash
curl http://127.0.0.1:8080/api/claims \
  -H "Authorization: Bearer $RESEARCHOS_ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"statement":"A candidate line design raises capacity.","provenance":"Synthetic engineering model","critical":false}'
```

Evidence scores are finite numbers from 0 to 1. Independent origin groups should identify underlying experiments or sources, not URLs that repeat the same material. Recorded check methods should reference reproducible artifacts. Tokens identify shared role accounts in this prototype; per-user attribution and external verification of executor independence are not provided.
