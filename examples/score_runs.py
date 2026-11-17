"""Aggregate measured run rows; never generate claimed model/human results."""
import argparse
import json
import math


def aggregate(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('nonempty row list required')
    groups, seen = {}, set()
    for row in rows:
        condition = row.get('condition')
        task = row.get('task_id')
        if condition not in ('A','B','C','D') or not isinstance(task,str) or not task:
            raise ValueError('condition A–D and nonempty task_id required')
        key = (condition,task)
        if key in seen:
            raise ValueError('duplicate condition/task pair')
        seen.add(key)
        for field in ('correct','accepted','reproduced','failure_present','failure_detected'):
            if not isinstance(row.get(field),bool):
                raise ValueError(field+' must be boolean')
        for field in ('seconds','reviewer_hours'):
            value=row.get(field)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0 or (field=='seconds' and value==0):
                raise ValueError(field+' invalid')
        if row['failure_detected'] and not row['failure_present']:
            raise ValueError('detection requires a known failure')
        groups.setdefault(condition,[]).append(row)
    results={}
    for condition, runs in groups.items():
        accepted=sum(r['accepted'] for r in runs)
        correct=sum(r['accepted'] and r['correct'] for r in runs)
        failures=sum(r['failure_present'] for r in runs)
        hours=sum(r['seconds'] for r in runs)/3600
        results[condition]={'tasks':len(runs),'accepted':accepted,'correct_accepted':correct,
            'correct_accepted_per_hour':correct/hours,
            'accepted_false_claim_rate':(accepted-correct)/accepted if accepted else None,
            'reproduction_rate':sum(r['accepted'] and r['reproduced'] for r in runs)/accepted if accepted else None,
            'failure_detection_recall':sum(r['failure_detected'] for r in runs)/failures if failures else None,
            'reviewer_hours_per_correct_accepted':sum(r['reviewer_hours'] for r in runs)/correct if correct else None}
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    args=parser.parse_args()
    with open(args.input,encoding='utf-8') as file:
        print(json.dumps(aggregate(json.load(file)),indent=2,allow_nan=False))


if __name__=='__main__':
    main()
