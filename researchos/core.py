"""Persistent, transactional TECT state machine. No model confidence is proof of truth."""
import hashlib
import json
import math
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

STATES = ('GENERATED', 'UNVERIFIED', 'SUPPORTED', 'ADVERSARIAL_TEST', 'REPRODUCED',
          'VALIDATED', 'STABLE', 'ASSURED')
ATTACKS = ('contradiction', 'assumption_violation', 'source_poisoning')
ROLES = {'researcher', 'reviewer', 'admin'}
POLICY = {'version': 'tect-prototype-1', 'minimum_source_groups': 2,
          'required_attacks': list(ATTACKS), 'stability_scope': 'recorded attack classes only'}


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def require_text(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 10000:
        raise ValueError(f'{field} must be nonempty text (maximum 10000 characters)')
    return value.strip()


def score(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f'{field} must be a finite number between 0 and 1')
    return value


class Store:
    def __init__(self, path='researchos.db'):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.db.executescript('''
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS claims(id TEXT PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS ledger(seq INTEGER PRIMARY KEY, event TEXT NOT NULL,
          previous_hash TEXT NOT NULL, hash TEXT NOT NULL);
        ''')

    def close(self):
        self.db.close()

    def _get(self, claim_id):
        row = self.db.execute('SELECT data FROM claims WHERE id=?', (claim_id,)).fetchone()
        if not row:
            raise KeyError('claim not found')
        return json.loads(row['data'])

    def get(self, claim_id):
        with self.lock:
            return self._get(claim_id)

    def claims(self):
        with self.lock:
            return [json.loads(r['data']) for r in self.db.execute('SELECT data FROM claims ORDER BY rowid')]

    def _save(self, c):
        self.db.execute('INSERT OR REPLACE INTO claims VALUES (?,?)', (c['id'], canonical(c)))

    def _log(self, actor, kind, claim_id, detail):
        row = self.db.execute('SELECT hash FROM ledger ORDER BY seq DESC LIMIT 1').fetchone()
        previous = row['hash'] if row else '0' * 64
        event = {'timestamp': now(), 'actor': actor, 'kind': kind, 'claim_id': claim_id, 'detail': detail}
        encoded = canonical(event)
        digest = hashlib.sha256((previous + encoded).encode()).hexdigest()
        self.db.execute('INSERT INTO ledger(event,previous_hash,hash) VALUES (?,?,?)', (encoded, previous, digest))

    def ledger(self):
        with self.lock:
            return [dict(r) | {'event': json.loads(r['event'])} for r in self.db.execute('SELECT * FROM ledger ORDER BY seq')]

    def verify_ledger(self):
        previous = '0' * 64
        for r in self.ledger():
            if r['previous_hash'] != previous or r['hash'] != hashlib.sha256((previous + canonical(r['event'])).encode()).hexdigest():
                return False
            previous = r['hash']
        return True

    def create(self, statement, provenance, actor='local', role='researcher', critical=False):
        statement = require_text(statement, 'statement')
        provenance = require_text(provenance, 'provenance')
        if role not in ROLES:
            raise PermissionError('unknown role')
        if not isinstance(critical, bool):
            raise ValueError('critical must be boolean')
        c = {'id': str(uuid.uuid4()), 'version': 1, 'statement': statement, 'provenance': provenance,
             'critical': critical, 'state': 'GENERATED', 'evidence': [], 'checks': [], 'dependencies': [],
             'challenges': [], 'created_at': now(), 'updated_at': now(), 'last_validation_at': None}
        with self.lock, self.db:
            self._save(c)
            self._log(actor, 'created', c['id'], c)
        return c

    def _invalidate(self, root, actor, reason):
        """Invalidate all transitive dependents and stale their earlier checks."""
        pending, seen = [root], {root}
        while pending:
            current = pending.pop()
            for c in self.claims():
                if current in c['dependencies'] and c['id'] not in seen:
                    seen.add(c['id'])
                    pending.append(c['id'])
                    c['state'] = 'CONTESTED'
                    c['version'] += 1
                    c['updated_at'] = now()
                    self._save(c)
                    self._log(actor, 'dependency_invalidated', c['id'], {'source': root, 'reason': reason})

    def mutate(self, claim_id, kind, data, actor='local', role='researcher'):
        if role not in ROLES:
            raise PermissionError('unknown role')
        with self.lock, self.db:
            c = self._get(claim_id)
            if kind == 'evidence':
                e = {k: require_text(data.get(k), k) for k in ('source', 'source_group', 'method', 'result')}
                for k in ('quality', 'reliability', 'independence'):
                    e[k] = score(data.get(k), k)
                e.update(id=str(uuid.uuid4()), timestamp=now(), actor=actor)
                c['evidence'].append(e)
            elif kind == 'dependency':
                other = require_text(data.get('claim_id'), 'claim_id')
                self._get(other)
                pending, visited = [other], set()
                while pending:
                    node = pending.pop()
                    if node == claim_id:
                        raise ValueError('dependency cycles are not permitted')
                    if node not in visited:
                        visited.add(node)
                        pending.extend(self._get(node)['dependencies'])
                if other in c['dependencies']:
                    raise ValueError('dependency already exists')
                c['dependencies'].append(other)
            elif kind == 'challenge':
                attack = data.get('attack')
                if attack not in ATTACKS:
                    raise ValueError('unknown attack class')
                c['challenges'].append({'id': str(uuid.uuid4()), 'attack': attack,
                    'detail': require_text(data.get('detail'), 'detail'), 'resolved': False, 'actor': actor, 'timestamp': now()})
                c['state'] = 'CONTESTED'
            elif kind == 'resolve':
                if role not in ('reviewer', 'admin'):
                    raise PermissionError('reviewer required to resolve challenges')
                challenge = next((x for x in c['challenges'] if x['id'] == data.get('challenge_id')), None)
                if not challenge or challenge['resolved']:
                    raise ValueError('open challenge not found')
                challenge.update(resolved=True, resolution=require_text(data.get('resolution'), 'resolution'), resolved_by=actor)
            elif kind == 'check':
                if role not in ('reviewer', 'admin'):
                    raise PermissionError('reviewer required to record checks')
                if data.get('kind') not in ('validation', 'reproduction', 'adversarial') or data.get('outcome') not in ('PASS', 'FAIL', 'UNCERTAIN'):
                    raise ValueError('invalid check kind or outcome')
                check = {k: require_text(data.get(k), k) for k in ('kind', 'outcome', 'method', 'runner', 'source_group')}
                if check['kind'] == 'adversarial':
                    if data.get('attack') not in ATTACKS:
                        raise ValueError('unknown attack class')
                    check['attack'] = data['attack']
                check.update(actor=actor, timestamp=now(), version=c['version'])
                c['checks'].append(check)
                if check['outcome'] != 'PASS':
                    c['state'] = 'CONTESTED'
                    self._invalidate(claim_id, actor, check['outcome'])
                c['updated_at'] = now()
                self._save(c)
                self._log(actor, kind, claim_id, check)
                return c
            else:
                raise ValueError('unknown operation')
            # Every material graph/evidence/challenge change makes earlier checks stale.
            c['version'] += 1
            if c['state'] != 'CONTESTED':
                c['state'] = 'UNVERIFIED'
            c['updated_at'] = now()
            self._save(c)
            self._log(actor, kind, claim_id, data)
            self._invalidate(claim_id, actor, kind)
            return c

    def metrics(self, c):
        # Conservative provenance clustering: duplicated groups contribute once.
        groups = {}
        for e in c['evidence']:
            value = e['quality'] * e['reliability'] * e['independence']
            groups[e['source_group']] = max(groups.get(e['source_group'], 0), value)
        density = sum(groups.values()) / (1 + len(c['dependencies']))
        open_challenges = sum(not x['resolved'] for x in c['challenges'])
        return {'validation_density': density, 'effective_source_groups': sum(v > 0 for v in groups.values()),
                'open_challenges': open_challenges, 'potential': int(not groups) + open_challenges + int(not c['provenance']),
                'assurance_is_truth': False}

    def _reasons(self, c, target, role):
        reasons = []
        if target not in STATES and target != 'UNVERIFIED':
            return ['unknown target state']
        current = c['state']
        expected = 'UNVERIFIED' if current == 'CONTESTED' else (STATES[STATES.index(current) + 1] if current != 'ASSURED' else None)
        if target != expected:
            reasons.append(f'next permitted state is {expected or "none"}')
        if role not in ROLES or (target in ('VALIDATED', 'STABLE', 'ASSURED') and role not in ('reviewer', 'admin')):
            reasons.append('actor role cannot perform this transition')
        if any(not x['resolved'] for x in c['challenges']):
            reasons.append('unresolved challenge')
        checks = [x for x in c['checks'] if x['version'] == c['version']]
        latest = {}
        for check in checks:
            latest[(check['kind'], check.get('attack'))] = check
        if any(x['outcome'] != 'PASS' for x in latest.values()):
            reasons.append('latest check is FAIL or UNCERTAIN')
        rank = STATES.index(target) if target in STATES else 0
        if rank >= STATES.index('SUPPORTED') and self.metrics(c)['effective_source_groups'] < POLICY['minimum_source_groups']:
            reasons.append('two positive independent source groups required')
        if rank >= STATES.index('REPRODUCED'):
            for attack in ATTACKS:
                if latest.get(('adversarial', attack), {}).get('outcome') != 'PASS':
                    reasons.append(f'missing passing adversarial check: {attack}')
            rep = latest.get(('reproduction', None), {})
            evidence_groups = {x['source_group'] for x in c['evidence']}
            if rep.get('outcome') != 'PASS' or rep.get('source_group') in evidence_groups:
                reasons.append('passing reproduction from a separate source group required')
        if rank >= STATES.index('VALIDATED'):
            if latest.get(('validation', None), {}).get('outcome') != 'PASS':
                reasons.append('passing validation required')
            for dependency in c['dependencies']:
                state = self._get(dependency)['state']
                if state not in ('VALIDATED', 'STABLE', 'ASSURED'):
                    reasons.append(f'dependency {dependency} is not validated')
        if target == 'ASSURED' and c['critical'] and role != 'admin':
            reasons.append('critical claim requires admin approval')
        return reasons

    def transition(self, claim_id, target, actor='local', role='researcher'):
        with self.lock, self.db:
            c = self._get(claim_id)
            reasons = self._reasons(c, target, role)
            accepted = not reasons
            self._log(actor, 'transition', claim_id, {'from': c['state'], 'to': target,
                'accepted': accepted, 'reasons': reasons, 'policy': POLICY, 'version': c['version'], 'role': role})
            if accepted:
                c['state'] = target
                c['updated_at'] = now()
                if target == 'VALIDATED':
                    c['last_validation_at'] = now()
                self._save(c)
            return {'accepted': accepted, 'reasons': reasons, 'claim': c}

    def assurance(self, claim_id):
        with self.lock:
            c = self._get(claim_id)
            return {'schema_version': '1.0', 'policy': POLICY, 'claim': c, 'metrics': self.metrics(c),
                    'ledger_valid': self.verify_ledger(), 'ledger_scope': 'complete local ledger',
                    'ledger': self.ledger(), 'limitations': ['Recorded checks are reviewer attestations.',
                    'Source independence is declared, not inferred.', 'Stability covers only the three recorded attack classes.',
                    'Hash chaining detects edits relative to a trusted head; it does not prevent database owner tampering.',
                    'No claim of calibrated truth probability or formal convergence.']}
