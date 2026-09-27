"""Bounded exhaustive seating optimization over accepted reservation terms."""
from datetime import datetime, timezone
from .validation import APIError


def interval(start, end):
    return (datetime.fromisoformat(start).astimezone(timezone.utc),
            datetime.fromisoformat(end).astimezone(timezone.utc))


def intersects(a, b):
    return a[0] < b[1] and b[0] < a[1]


def blocked(record, ids, closures):
    span = interval(record['starts_at'], record['ends_at'])
    return any(c['restaurant_id'] == record['restaurant_id'] and c['table_id'] in ids
               and intersects(span, interval(c['from'], c['to'])) for c in closures)


def solve(restaurant, bookings, closures, proposed):
    span = interval(proposed['from'], proposed['to'])
    active = [r for r in bookings if r['restaurant_id'] == restaurant['id'] and r['status'] == 'confirmed']
    considered = sorted([r for r in active if intersects(span, interval(r['starts_at'], r['ends_at']))], key=lambda r: r['reference'])
    if len(restaurant['tables']) > 6 or len(restaurant.get('combinable', [])) > 4 or len(considered) > 6:
        raise APIError(422, 'planning_limit')
    refs = {r['reference'] for r in considered}
    fixed = [r for r in active if r['reference'] not in refs]
    options = [[t['id']] for t in restaurant['tables']] + restaurant.get('combinable', [])
    spans = [interval(r['starts_at'], r['ends_at']) for r in considered]
    candidates = []
    for i, record in enumerate(considered):
        choices = []
        for rank, ids in enumerate(options):
            capacity = sum(record['accepted_terms']['capacities'][tid] for tid in ids)
            if capacity < record['party_size'] or blocked(record, ids, [*closures, proposed]):
                continue
            if any(set(ids).intersection(r['table_ids']) and intersects(spans[i], interval(r['starts_at'], r['ends_at'])) for r in fixed):
                continue
            choices.append((rank, ids, int(ids != record['table_ids']), capacity - record['party_size']))
        candidates.append(choices)
    best = None
    best_choices = None
    chosen = []
    def visit(index, moved, unused):
        nonlocal best, best_choices
        if best is not None and (moved > best[0] or (moved == best[0] and unused > best[1])):
            return
        if index == len(considered):
            score = (moved, unused, tuple(c[0] for c in chosen))
            if best is None or score < best:
                best, best_choices = score, list(chosen)
            return
        for choice in candidates[index]:
            if any(set(choice[1]).intersection(previous[1]) and intersects(spans[index], spans[j]) for j, previous in enumerate(chosen)):
                continue
            chosen.append(choice)
            visit(index + 1, moved + choice[2], unused + choice[3])
            chosen.pop()
    visit(0, 0, 0)
    if best is None:
        raise APIError(409, 'no_feasible_plan')
    assignments = [{'reference': r['reference'], 'table_ids': list(c[1]), 'changed': bool(c[2])} for r, c in zip(considered, best_choices)]
    return considered, assignments, best[0], best[1]
