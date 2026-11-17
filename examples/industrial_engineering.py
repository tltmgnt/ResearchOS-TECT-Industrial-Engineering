"""Synthetic line-balancing pilot. Run: python -m examples.industrial_engineering."""
import argparse
import json
from pathlib import Path
from researchos.core import Store, STATES
from researchos.operators import run_attacks


def demo(store):
    c = store.create('Synthetic line redesign increases capacity from 60 to 75 units/hour.',
                     'Synthetic deterministic fixture, not an observed factory result', 'demo', 'researcher')
    claim_id = c['id']
    # Independent arithmetic methods; source independence is an explicit synthetic assumption.
    baseline_seconds, proposed_seconds = 60, 48
    assert 3600 / baseline_seconds == 60 and 3600 / proposed_seconds == 75
    for source, group in [('Cycle-time calculation', 'analytical-model'), ('Independent event schedule', 'schedule-model')]:
        store.mutate(claim_id, 'evidence', {'source': source, 'source_group': group,
            'method': 'Synthetic capacity = 3600 / bottleneck seconds', 'result': '60 → 75 units/hour under deterministic assumptions',
            'quality': 1, 'reliability': 1, 'independence': 1}, 'demo')
    for target in ('SUPPORTED', 'ADVERSARIAL_TEST'):
        assert store.transition(claim_id, target, 'demo')['accepted']
    run_attacks(store, claim_id, 'demo-reviewer', 'reviewer')
    # Separate discrete-event arithmetic: 75 completions at 48-second intervals.
    assert len(list(range(48, 3601, 48))) == 75
    for kind in ('reproduction', 'validation'):
        store.mutate(claim_id, 'check', {'kind': kind, 'outcome': 'PASS', 'method': 'Independent deterministic completion schedule; 75 units in one hour',
            'runner': 'synthetic-schedule-check', 'source_group': 'independent-reproduction'}, 'demo-reviewer', 'reviewer')
    for target in STATES[4:]:
        assert store.transition(claim_id, target, 'demo-reviewer', 'reviewer')['accepted']
    return store.assurance(claim_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='researchos.db')
    parser.add_argument('--output', default='artifacts/industrial-assurance.json')
    args = parser.parse_args()
    store = Store(args.db)
    try:
        record = demo(store)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, indent=2), encoding='utf-8')
        print(json.dumps({'claim_id': record['claim']['id'], 'state': record['claim']['state'], 'output': str(output),
                          'warning': 'Synthetic demonstration; not measured discovery or robustness performance.'}))
    finally:
        store.close()


if __name__ == '__main__':
    main()
