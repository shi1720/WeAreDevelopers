"""Recurring adoption and membership transitions inside the caller's transaction."""
from copy import deepcopy
from datetime import datetime, timedelta
import secrets
from .validation import APIError, identifier, invalid


def owned(state, user, sid):
    agreement = state['series'].get(sid)
    if agreement is None or agreement['user_id'] != user:
        raise APIError(404, 'not_found')
    return agreement


def response(state, agreement):
    from .reservations import public
    return {'series_id': agreement['series_id'], 'revision': agreement['revision'],
            'interval_weeks': agreement['interval_weeks'],
            'occurrences': [{'index': o['index'], 'reference': o['reference'], 'exception': o['exception'],
                'reservation': public(state['reservations'][o['reference']])} for o in agreement['occurrences']]}


def touch(state, references, *, exception=False):
    refs = set(references)
    for agreement in state['series'].values():
        affected = [o for o in agreement['occurrences'] if o['reference'] in refs]
        if affected:
            agreement['revision'] += 1
            if exception:
                for occurrence in affected:
                    occurrence['exception'] = True


def adopt(state, user, body):
    from . import reservations
    reference = identifier(body, 'anchor_reference')
    count, interval = body.get('count'), body.get('interval_weeks')
    if type(count) is not int or not 2 <= count <= 12 or type(interval) is not int or not 1 <= interval <= 4:
        invalid('Count must be 2..12 and interval_weeks 1..4')
    anchor = reservations.owned(state, user, reference)
    restaurant = reservations.restaurant_for(state, anchor['restaurant_id'])
    reservations.editable(anchor, restaurant)
    if any(o['reference'] == reference for s in state['series'].values() for o in s['occurrences']):
        raise APIError(409, 'already_in_series')
    local = datetime.fromisoformat(anchor['starts_at_local'])
    occurrences = [{'index': 0, 'reference': reference, 'exception': False, 'scheduled_date': local.date().isoformat()}]
    for index in range(1, count):
        try:
            scheduled = local + timedelta(weeks=index * interval)
        except OverflowError:
            invalid('Recurring date exceeds calendar range')
        item = {'restaurant_id': anchor['restaurant_id'], 'table_ids': deepcopy(anchor['table_ids']),
                'party_size': anchor['party_size'], 'starts_at_local': scheduled.isoformat(timespec='minutes')}
        booking = reservations.create(state, user, item, bump=False)
        occurrences.append({'index': index, 'reference': booking['reference'], 'exception': False,
                            'scheduled_date': scheduled.date().isoformat()})
    sid = 'series_' + secrets.token_hex(16)
    agreement = {'series_id': sid, 'revision': 1, 'interval_weeks': interval, 'user_id': user,
                 'restaurant_id': anchor['restaurant_id'], 'occurrences': occurrences}
    state['series'][sid] = agreement
    state['restaurant_revisions'][anchor['restaurant_id']] += 1
    return response(state, agreement)


def amend(state, user, sid, body):
    from . import reservations, history
    import re
    agreement = owned(state, user, sid)
    expected, first, clock = (body.get(k) for k in ('expected_revision', 'from_index', 'local_time'))
    if (type(expected) is not int or expected < 1 or type(first) is not int
            or not 0 <= first < len(agreement['occurrences']) or type(clock) is not str
            or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', clock)):
        invalid('Invalid recurring amendment')
    if expected != agreement['revision']:
        raise APIError(409, 'stale_revision')
    before = response(state, agreement)
    candidates = []
    for occurrence in agreement['occurrences'][first:]:
        old = state['reservations'][occurrence['reference']]
        if occurrence['exception'] or old['status'] == 'cancelled':
            continue
        local = occurrence['scheduled_date'] + 'T' + clock
        if local == old['starts_at_local']:
            candidates.append(deepcopy(old))
            continue
        reservations.editable(old, reservations.restaurant_for(state, old['restaurant_id']))
        candidates.append(reservations.candidate(state, {'starts_at_local': local}, old))
    reservations.check_occupancy(state, candidates, [r['reference'] for r in candidates])
    changed = []
    for record in candidates:
        old = state['reservations'][record['reference']]
        if history.changes(old, record):
            record['revision'] += 1
            history.append(state, record, 'changed', old)
            state['reservations'][record['reference']] = record
            changed.append(record['reference'])
    if changed:
        agreement['revision'] += 1
        state['restaurant_revisions'][agreement['restaurant_id']] += 1
    result = response(state, agreement)
    # Portable provenance lets import distinguish collective clock amendments
    # from permanent individual diner exceptions without changing public history.
    state['series_operations'].append({'series_id': sid, 'body': deepcopy(body),
                                       'before': before, 'after': deepcopy(result)})
    return result
