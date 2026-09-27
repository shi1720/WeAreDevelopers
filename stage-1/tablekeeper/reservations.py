"""Reservation operations. The caller owns the state transaction."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import secrets
from .validation import APIError, field, identifier, invalid, party_size, canonical
from .temporal import booking_interval
from .availability import overlaps


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


def editable(record, restaurant):
    if record['status'] == 'cancelled':
        raise APIError(409, 'reservation_cancelled')
    cutoff(record, restaurant)


def cutoff(record, restaurant):
    start = datetime.fromisoformat(record['starts_at']).astimezone(timezone.utc)
    if now() >= start - timedelta(minutes=restaurant['cancellation_cutoff_minutes']):
        raise APIError(409, 'cutoff_passed')


def candidate(state, body, current=None):
    rid = current['restaurant_id'] if current else identifier(body, 'restaurant_id')
    restaurant = restaurant_for(state, rid)
    tid = identifier(body, 'table_id') if current is None or 'table_id' in body else current['table_id']
    table = next((t for t in restaurant['tables'] if t['id'] == tid), None)
    if table is None:
        raise APIError(404, 'not_found')
    if current is None and 'party_size' not in body:
        invalid('Missing party_size')
    size = party_size(body['party_size'] if 'party_size' in body else current['party_size'])
    local = field(body, 'starts_at_local') if current is None or 'starts_at_local' in body else current['starts_at_local']
    start, end = booking_interval(restaurant, local)
    if size > table['capacity']:
        raise APIError(422, 'party_exceeds_capacity')
    if current is not None and (tid, size, local) == (current['table_id'], current['party_size'], current['starts_at_local']):
        return deepcopy(current)
    result = deepcopy(current) if current else {}
    result.update(restaurant_id=rid, table_id=tid, party_size=size,
                  starts_at_local=local, starts_at=start.isoformat(), ends_at=end.isoformat())
    return result


def check_occupancy(state, candidates, excluded=()):
    others = [r for ref, r in state['reservations'].items() if ref not in excluded and r['status'] == 'confirmed']
    for record in candidates:
        start, end = datetime.fromisoformat(record['starts_at']), datetime.fromisoformat(record['ends_at'])
        for other in others:
            if (other['restaurant_id'] == record['restaurant_id'] and other['table_id'] == record['table_id']
                    and overlaps(start, end, other)):
                raise APIError(409, 'table_unavailable')
        others.append(record)


def create(state, user, body):
    record = candidate(state, body)
    check_occupancy(state, [record])
    reference = secrets.token_hex(5).upper()
    while reference in state['reservations']:
        reference = secrets.token_hex(5).upper()
    record.update(reservation_id='res_' + secrets.token_hex(16), reference=reference,
                  user_id=user, status='confirmed', created_at=now().isoformat())
    state['reservations'][reference] = record
    return public(record)


def amend(state, user, reference, body):
    old = owned(state, user, reference)
    editable(old, restaurant_for(state, old['restaurant_id']))
    changed = candidate(state, body, old)
    check_occupancy(state, [changed], [reference])
    state['reservations'][reference] = changed
    return public(changed)


def cancel(state, user, reference):
    record = owned(state, user, reference)
    if record['status'] != 'cancelled':
        cutoff(record, restaurant_for(state, record['restaurant_id']))
        record['status'] = 'cancelled'
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
        editable(old, restaurant_for(state, rid))
        candidates.append(candidate(state, item, old))
    check_occupancy(state, candidates, refs)
    for record in candidates:
        state['reservations'][record['reference']] = record
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
