"""Reservation operations. The caller owns the state transaction."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import secrets
from .validation import APIError, field, identifier, invalid, party_size, canonical
from .temporal import booking_interval
from .availability import overlaps
from . import history, policies


def now():
    return datetime.now(timezone.utc)


def public(record):
    return {k: deepcopy(v) for k, v in record.items() if k != 'user_id'}


def restaurant_for(state, rid):
    restaurant = next((r for r in state['restaurants'] if r['id'] == rid), None)
    if restaurant is None:
        raise APIError(404, 'not_found')
    return restaurant


def owned(state, user, reference):
    record = state['reservations'].get(reference)
    if record is None or record['user_id'] != user:
        raise APIError(404, 'not_found')
    return record


def editable(record, restaurant, body=None):
    if body is not None and 'expected_revision' in body:
        expected = body['expected_revision']
        if type(expected) is not int or expected < 1:
            invalid('expected_revision must be a positive integer')
        if expected != record['revision']:
            raise APIError(409, 'stale_revision')
    if record['status'] == 'cancelled':
        raise APIError(409, 'reservation_cancelled')
    cutoff(record, restaurant)


def cutoff(record, restaurant):
    start = datetime.fromisoformat(record['starts_at']).astimezone(timezone.utc)
    cutoff_minutes = record.get('accepted_terms', restaurant)['cancellation_cutoff_minutes']
    if now() >= start - timedelta(minutes=cutoff_minutes):
        raise APIError(409, 'cutoff_passed')


def table_ids(record):
    return record['table_ids'] if 'table_ids' in record else [record['table_id']]


def selection(restaurant, body, current=None):
    """Resolve one or two tables into their canonical declared order."""
    if 'table_id' in body and 'table_ids' in body:
        invalid('Use table_id or table_ids, not both')
    if 'table_ids' in body:
        ids = field(body, 'table_ids', list)
        if not ids:
            invalid('Select at least one table')
        if len(ids) > 2:
            raise APIError(422, 'combination_not_allowed')
        for tid in ids:
            if type(tid) is not str:
                raise APIError(400, 'malformed_request', 'Table ids must be strings')
            if not tid or len(tid) > 64:
                invalid('Invalid table id')
        if len(set(ids)) != len(ids):
            invalid('Duplicate table id')
    elif 'table_id' in body:
        ids = [identifier(body, 'table_id')]
    elif current is not None:
        ids = table_ids(current)
    else:
        invalid('Missing table selection')
    tables = {t['id']: t for t in restaurant['tables']}
    if any(tid not in tables for tid in ids):
        raise APIError(404, 'not_found')
    if len(ids) == 2:
        pair = next((p for p in restaurant.get('combinable', []) if set(p) == set(ids)), None)
        if pair is None:
            raise APIError(422, 'combination_not_allowed')
        ids = pair
    return list(ids), sum(tables[tid]['capacity'] for tid in ids)


def candidate(state, body, current=None, terms=None):
    rid = current['restaurant_id'] if current else identifier(body, 'restaurant_id')
    restaurant = restaurant_for(state, rid)
    ids, _ = selection(restaurant, body, current)
    if current is None and 'party_size' not in body:
        invalid('Missing party_size')
    size = party_size(body['party_size'] if 'party_size' in body else current['party_size'])
    local = field(body, 'starts_at_local') if current is None or 'starts_at_local' in body else current['starts_at_local']
    if current is not None and (ids, size, local) == (table_ids(current), current['party_size'], current['starts_at_local']):
        return deepcopy(current)
    accepted = deepcopy(terms) if terms is not None else policies.select_terms(state, restaurant, local[:10])
    effective = policies.effective_restaurant(restaurant, accepted)
    start, end = booking_interval(effective, local)
    capacity = sum(accepted['capacities'][tid] for tid in ids)
    if size > capacity:
        raise APIError(422, 'party_exceeds_capacity')
    result = deepcopy(current) if current else {}
    result.pop('table_id', None)
    result.update(restaurant_id=rid, table_ids=ids, party_size=size,
                  starts_at_local=local, starts_at=start.isoformat(), ends_at=end.isoformat())
    if len(ids) == 1:
        result['table_id'] = ids[0]
    result['accepted_terms'] = accepted
    return result


def check_occupancy(state, candidates, excluded=()):
    others = [r for ref, r in state['reservations'].items() if ref not in excluded and r['status'] == 'confirmed']
    for record in candidates:
        start, end = datetime.fromisoformat(record['starts_at']), datetime.fromisoformat(record['ends_at'])
        for other in others:
            if (other['restaurant_id'] == record['restaurant_id'] and set(table_ids(other)).intersection(table_ids(record))
                    and overlaps(start, end, other)):
                raise APIError(409, 'table_unavailable')
        others.append(record)


def create(state, user, body, *, bump=True):
    record = candidate(state, body)
    check_occupancy(state, [record])
    reference = secrets.token_hex(5).upper()
    while reference in state['reservations']:
        reference = secrets.token_hex(5).upper()
    record.update(reservation_id='res_' + secrets.token_hex(16), reference=reference,
                  user_id=user, status='confirmed', created_at=now().isoformat(), revision=1)
    state['reservations'][reference] = record
    history.initialize(state, record)
    if bump:
        state['restaurant_revisions'][record['restaurant_id']] += 1
    return public(record)


def amend(state, user, reference, body):
    old = owned(state, user, reference)
    editable(old, restaurant_for(state, old['restaurant_id']), body)
    changed = candidate(state, body, old)
    check_occupancy(state, [changed], [reference])
    if history.changes(old, changed):
        changed['revision'] += 1
        state['reservations'][reference] = changed
        history.append(state, changed, 'changed', old)
        state['restaurant_revisions'][changed['restaurant_id']] += 1
        from .series import touch
        touch(state, [reference], exception=True)
    return public(changed)


def cancel(state, user, reference):
    record = owned(state, user, reference)
    if record['status'] != 'cancelled':
        cutoff(record, restaurant_for(state, record['restaurant_id']))
        record['status'] = 'cancelled'
        record['revision'] += 1
        history.append(state, record, 'cancelled')
        state['restaurant_revisions'][record['restaurant_id']] += 1
        from .series import touch
        touch(state, [reference])
    return public(record)


def moves(state, user, body):
    items = body.get('moves')
    if type(items) is not list or not 1 <= len(items) <= 8:
        invalid('Expected one to eight moves')
    refs = []
    for item in items:
        if type(item) is not dict or type(item.get('reference')) is not str:
            invalid('Each move requires a reference')
        ref = item['reference']
        if not ref or len(ref) > 64 or ref in refs:
            invalid('References must be distinct')
        refs.append(ref)
    candidates = []
    rid = None
    for item in items:
        old = owned(state, user, item['reference'])
        if rid is not None and old['restaurant_id'] != rid:
            invalid('All moves must share a restaurant')
        rid = old['restaurant_id']
        editable(old, restaurant_for(state, rid), item)
        candidates.append(candidate(state, item, old))
    check_occupancy(state, candidates, refs)
    changed_refs = []
    for record in candidates:
        old = state['reservations'][record['reference']]
        if history.changes(old, record):
            record['revision'] += 1
            history.append(state, record, 'changed', old)
            state['reservations'][record['reference']] = record
            changed_refs.append(record['reference'])
    if changed_refs:
        state['restaurant_revisions'][rid] += 1
        from .series import touch
        touch(state, changed_refs, exception=True)
    return {'reservations': [public(r) for r in candidates]}


def idempotent(state, user, method, path, key, body, operation):
    if key is None or key == '':
        raise APIError(400, 'missing_idempotency_key')
    if len(key) > 255:
        invalid('Idempotency key exceeds 255 characters')
    receipt = next((r for r in state['receipts'] if (r['user_id'], r['method'], r['path'], r['key'])
                    == (user, method, path, key)), None)
    if receipt is not None:
        if canonical(receipt['body']) != canonical(body):
            raise APIError(409, 'idempotency_key_reuse')
        return 200, deepcopy(receipt['response'])
    response = operation()
    state['receipts'].append({'user_id': user, 'method': method, 'path': path, 'key': key,
                              'body': deepcopy(body), 'response': deepcopy(response)})
    return 201, response
