"""Independent exhaustive seating oracle: no application imports or search pruning."""
from datetime import datetime
from itertools import product


def overlaps(a, b):
    return datetime.fromisoformat(a[0]) < datetime.fromisoformat(b[1]) and datetime.fromisoformat(b[0]) < datetime.fromisoformat(a[1])


def solve(restaurant, bookings, closure, existing=()):
    options = [(t['id'],) for t in restaurant['tables']] + [tuple(p) for p in restaurant.get('combinable', [])]
    interval = (closure['from'], closure['to'])
    live = [b for b in bookings if b['status'] == 'confirmed' and b['restaurant_id'] == restaurant['id']]
    considered = sorted([b for b in live if overlaps((b['starts_at'], b['ends_at']), interval)], key=lambda b: b['reference'])
    fixed = [b for b in live if b not in considered]
    choices = []
    for booking in considered:
        span = (booking['starts_at'], booking['ends_at'])
        choices.append([rank for rank, option in enumerate(options)
                        if sum(booking['accepted_terms']['capacities'][t] for t in option) >= booking['party_size']
                        and not any(c['table_id'] in option and overlaps(span, (c['from'], c['to'])) for c in [*existing, closure])
                        and not any(set(option) & set(b['table_ids']) and overlaps(span, (b['starts_at'], b['ends_at'])) for b in fixed)])
    best = None
    for ranks in product(*choices):
        if any(set(options[ranks[i]]) & set(options[ranks[j]]) and overlaps((considered[i]['starts_at'], considered[i]['ends_at']), (considered[j]['starts_at'], considered[j]['ends_at']))
               for i in range(len(considered)) for j in range(i)):
            continue
        changed = [set(options[rank]) != set(b['table_ids']) for rank, b in zip(ranks, considered)]
        unused = sum(sum(b['accepted_terms']['capacities'][t] for t in options[rank]) - b['party_size'] for rank, b in zip(ranks, considered))
        score = (sum(changed), unused, ranks)
        if best is None or score < best[0]:
            best = (score, [{'reference': b['reference'], 'table_ids': list(options[rank]), 'changed': changed[i]} for i, (rank, b) in enumerate(zip(ranks, considered))])
    return None if best is None else {'assignments': best[1], 'moved_count': best[0][0], 'unused_seats': best[0][1]}
