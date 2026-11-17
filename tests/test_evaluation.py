import unittest
from examples.score_runs import aggregate

class EvaluationTests(unittest.TestCase):
    def row(self, **kw):
        return dict(condition='D',task_id='t',seconds=60,reviewer_hours=.1,correct=False,accepted=True,reproduced=False,failure_present=True,failure_detected=True) | kw

    def test_false_acceptance_and_detection(self):
        result=aggregate([self.row()])['D']
        self.assertEqual(result['accepted_false_claim_rate'],1)
        self.assertEqual(result['failure_detection_recall'],1)
        self.assertIsNone(result['reviewer_hours_per_correct_accepted'])

    def test_abstention_and_no_failures_have_null_denominators(self):
        result=aggregate([self.row(accepted=False,failure_present=False,failure_detected=False)])['D']
        self.assertIsNone(result['accepted_false_claim_rate'])
        self.assertIsNone(result['failure_detection_recall'])

    def test_reject_invalid_runs(self):
        for rows in ([self.row(),self.row()],[self.row(seconds=float('nan'))],[self.row(failure_present=False)]):
            with self.assertRaises(ValueError):
                aggregate(rows)
