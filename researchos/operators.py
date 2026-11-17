"""Three deterministic screening operators. Passing is not a robustness certificate."""
from .core import ATTACKS


def run_attacks(store, claim_id, actor='local', role='reviewer'):
    if role not in ('reviewer', 'admin'):
        raise PermissionError('reviewer required to run attacks')
    c = store.get(claim_id)
    checks = []
    for attack in ATTACKS:
        if attack == 'contradiction':
            failed = any(not x['resolved'] and x['attack'] == attack for x in c['challenges'])
            explanation = 'Screen unresolved contradiction challenges'
        elif attack == 'source_poisoning':
            failed = store.metrics(c)['effective_source_groups'] < 2
            explanation = 'Collapse duplicated source groups; require two positive groups'
        else:
            failed = any(store.get(x)['state'] not in ('VALIDATED', 'STABLE', 'ASSURED') for x in c['dependencies'])
            explanation = 'Check whether declared dependency assumptions remain validated'
        result = store.mutate(claim_id, 'check', {'kind': 'adversarial', 'attack': attack,
            'outcome': 'FAIL' if failed else 'PASS', 'method': explanation,
            'runner': 'builtin-screen-v1', 'source_group': 'builtin-screen'}, actor, role)
        checks.append(result['checks'][-1])
    return {'checks': checks, 'scope': 'structural screens only; no semantic contradiction discovery or unseen attacks'}
