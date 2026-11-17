import json
import tempfile
import unittest
from pathlib import Path
from researchos.core import Store
from researchos.operators import run_attacks
from examples.industrial_engineering import demo


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(':memory:')

    def tearDown(self):
        self.store.close()

    def claim(self):
        return self.store.create('A testable claim', 'test fixture')['id']

    def evidence(self, claim_id, group='one'):
        return self.store.mutate(claim_id, 'evidence', dict(source='source', source_group=group,
            method='test', result='observation', quality=1, reliability=1, independence=1))

    def test_full_lifecycle_and_export(self):
        record = demo(self.store)
        self.assertEqual(record['claim']['state'], 'ASSURED')
        self.assertTrue(record['ledger_valid'])
        self.assertEqual(record['metrics']['effective_source_groups'], 2)
        json.dumps(record, allow_nan=False)

    def test_skipping_is_rejected_and_logged(self):
        c = self.claim()
        self.assertFalse(self.store.transition(c, 'ASSURED', role='admin')['accepted'])
        event = self.store.ledger()[-1]['event']
        self.assertFalse(event['detail']['accepted'])
        self.assertEqual(self.store.get(c)['state'], 'GENERATED')

    def test_correlated_sources_do_not_count_twice(self):
        c = self.claim()
        self.evidence(c)
        self.evidence(c)
        self.assertEqual(self.store.metrics(self.store.get(c))['effective_source_groups'], 1)
        self.assertFalse(self.store.transition(c, 'SUPPORTED')['accepted'])
        result = run_attacks(self.store, c)
        self.assertEqual(next(x for x in result['checks'] if x['attack']=='source_poisoning')['outcome'], 'FAIL')

    def test_new_evidence_stales_checks(self):
        c = demo(self.store)['claim']['id']
        self.evidence(c, 'three')
        self.assertEqual(self.store.get(c)['state'], 'UNVERIFIED')
        for target in ('SUPPORTED', 'ADVERSARIAL_TEST'):
            self.assertTrue(self.store.transition(c, target)['accepted'])
        self.assertFalse(self.store.transition(c, 'REPRODUCED', role='reviewer')['accepted'])

    def test_dependency_invalidation_is_transitive(self):
        a = demo(self.store)['claim']['id']
        b, c = self.claim(), self.claim()
        self.store.mutate(b, 'dependency', {'claim_id': a})
        self.store.mutate(c, 'dependency', {'claim_id': b})
        self.store.mutate(a, 'challenge', {'attack': 'contradiction', 'detail': 'counterexample'})
        for claim_id in (a,b,c):
            self.assertEqual(self.store.get(claim_id)['state'], 'CONTESTED')
        with self.assertRaises(ValueError):
            self.store.mutate(a, 'dependency', {'claim_id': c})

    def test_uncertain_blocks_acceptance(self):
        c = self.claim()
        self.evidence(c)
        self.evidence(c,'two')
        self.store.mutate(c, 'check', {'kind':'validation', 'outcome':'UNCERTAIN', 'method':'missing sample', 'runner':'tester', 'source_group':'test'}, role='reviewer')
        self.assertFalse(self.store.transition(c,'UNVERIFIED')['accepted'])
        self.assertEqual(self.store.get(c)['state'], 'CONTESTED')

    def test_unauthorized_check_cannot_change_claim(self):
        c = self.claim()
        with self.assertRaises(PermissionError):
            self.store.mutate(c, 'check', {}, role='researcher')
        self.assertEqual(self.store.get(c)['checks'], [])

    def test_critical_assurance_requires_admin(self):
        record = demo(self.store)
        c = record['claim']
        c['state'] = 'STABLE'
        c['critical'] = True
        with self.store.db:
            self.store._save(c)
        self.assertFalse(self.store.transition(c['id'],'ASSURED',role='reviewer')['accepted'])
        self.assertTrue(self.store.transition(c['id'],'ASSURED',role='admin')['accepted'])

    def test_challenge_resolution_requires_fresh_validation(self):
        c = demo(self.store)['claim']['id']
        updated = self.store.mutate(c,'challenge', {'attack':'contradiction','detail':'new report'})
        challenge_id=updated['challenges'][0]['id']
        with self.assertRaises(PermissionError):
            self.store.mutate(c,'resolve',{'challenge_id':challenge_id,'resolution':'checked'})
        self.store.mutate(c,'resolve',{'challenge_id':challenge_id,'resolution':'report disproven'}, role='reviewer')
        self.assertTrue(self.store.transition(c,'UNVERIFIED')['accepted'])
        self.assertFalse(self.store.transition(c,'ASSURED',role='admin')['accepted'])

    def test_tampering_detected(self):
        self.claim()
        with self.store.db:
            self.store.db.execute("UPDATE ledger SET event='{}' WHERE seq=1")
        self.assertFalse(self.store.verify_ledger())

    def test_nonfinite_and_invalid_inputs(self):
        c = self.claim()
        for value in (float('nan'),float('inf'), -1, 1.1, True):
            with self.assertRaises(ValueError):
                self.store.mutate(c,'evidence',dict(source='s',source_group='g',method='m',result='r',quality=value,reliability=1,independence=1))
        with self.assertRaises(KeyError):
            self.store.mutate(c, 'dependency', {'claim_id':'missing'})
        self.assertEqual(self.store.get(c)['version'], 1)

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp)/'db.sqlite')
            store = Store(path)
            c = store.create('persistent','fixture')
            store.close()
            reopened = Store(path)
            self.assertEqual(reopened.get(c['id'])['statement'], 'persistent')
            self.assertTrue(reopened.verify_ledger())
            reopened.close()


if __name__ == '__main__':
    unittest.main()
