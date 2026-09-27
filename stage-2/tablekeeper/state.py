"""Portable, validated state and atomic snapshot replacement."""
from copy import deepcopy
from datetime import datetime, timezone
import re
from threading import RLock
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .auth import hash_password, valid_hash
from .validation import APIError, invalid


def empty():
    return {'schema': 2, 'users': {}, 'tokens': {}, 'restaurants': [], 'reservations': {}, 'receipts': []}


def require(condition, message='Invalid state'):
    if not condition:
        invalid(message)


def ident(value):
    return type(value) is str and 1 <= len(value) <= 64


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def instant(value):
    require(type(value) is str)
    try:
        parsed = datetime.fromisoformat(value)
        require(parsed.tzinfo is not None)
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        invalid('Invalid timestamp')


def validate_restaurants(restaurants):
    require(type(restaurants) is list)
    ids = set()
    for restaurant in restaurants:
        require(type(restaurant) is dict)
        rid = restaurant.get('id')
        require(ident(rid) and rid not in ids)
        ids.add(rid)
        require(type(restaurant.get('name')) is str and type(restaurant.get('timezone')) is str)
        try:
            ZoneInfo(restaurant['timezone'])
        except (ZoneInfoNotFoundError, ValueError):
            invalid('Unknown timezone')
        for name in ('slot_minutes', 'reservation_duration_minutes'):
            require(integer(restaurant.get(name), 1))
        require(integer(restaurant.get('cancellation_cutoff_minutes')))
        require(type(restaurant.get('opening_hours')) is list)
        days = set()
        for hours in restaurant['opening_hours']:
            require(type(hours) is dict)
            day = hours.get('weekday')
            require(type(day) is str and day in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun') and day not in days)
            days.add(day)
            for name in ('opens', 'closes'):
                require(type(hours.get(name)) is str and re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', hours[name]) is not None)
            require(hours['opens'] < hours['closes'])
        require(type(restaurant.get('tables')) is list)
        tids = set()
        for table in restaurant['tables']:
            require(type(table) is dict)
            tid = table.get('id')
            require(ident(tid) and tid not in tids)
            tids.add(tid)
            require(type(table.get('label')) is str and integer(table.get('capacity'), 1))
        pairs = restaurant.get('combinable', [])
        require(type(pairs) is list)
        seen = set()
        for pair in pairs:
            require(type(pair) is list and len(pair) == 2 and all(ident(t) for t in pair))
            require(pair[0] != pair[1] and all(t in tids for t in pair))
            require(frozenset(pair) not in seen)
            seen.add(frozenset(pair))


def selection_body(record):
    """Records expose a singleton alias; request bodies may not send both."""
    body = deepcopy(record)
    if 'table_ids' in body:
        body.pop('table_id', None)
    return body


def validate_record(record, state, *, owner=None):
    from .reservations import candidate
    require(type(record) is dict)
    for name in ('reservation_id', 'reference', 'restaurant_id', 'user_id'):
        require(ident(record.get(name)))
    require(re.fullmatch('[A-Z0-9]{6,12}', record['reference']) is not None)
    require(record['user_id'] in state['users'])
    if owner is not None:
        require(record['user_id'] == owner)
    require(record.get('status') in ('confirmed', 'cancelled'))
    instant(record.get('created_at'))
    expected = candidate(state, selection_body(record))
    if 'table_ids' in record:
        require(record['table_ids'] == expected['table_ids'])
        if len(record['table_ids']) == 1:
            require(record.get('table_id') == record['table_ids'][0])
        else:
            require('table_id' not in record)
    else:
        # Original stage-1 receipts are immutable and legitimately lack table_ids.
        require(record.get('table_id') == expected.get('table_id'))
    require(instant(record.get('starts_at')) == instant(expected['starts_at']))
    require(instant(record.get('ends_at')) == instant(expected['ends_at']))


def validate_state(state):
    from .reservations import candidate, check_occupancy
    require(type(state) is dict and type(state.get('schema')) is int and state['schema'] == 2)
    require(type(state.get('users')) is dict and type(state.get('tokens')) is dict)
    emails = set()
    for uid, user in state['users'].items():
        require(ident(uid) and type(user) is dict and user.get('id') == uid)
        require(type(user.get('email')) is str and re.fullmatch(r'[^\s@]+@[^\s@]+', user['email']) is not None)
        require(user['email'] not in emails)
        emails.add(user['email'])
        require(type(user.get('display_name')) is str and valid_hash(user.get('password_hash')))
        require('password' not in user)
    for token, uid in state['tokens'].items():
        require(type(token) is str and token and not any(c.isspace() for c in token))
        require(type(uid) is str and uid in state['users'])
    validate_restaurants(state.get('restaurants'))
    require(type(state.get('reservations')) is dict)
    reservation_ids = set()
    for ref, record in state['reservations'].items():
        validate_record(record, state)
        require('table_ids' in record)
        require(record['reference'] == ref and record['reservation_id'] not in reservation_ids)
        reservation_ids.add(record['reservation_id'])
    confirmed = [r for r in state['reservations'].values() if r['status'] == 'confirmed']
    check_occupancy(state, confirmed, state['reservations'])
    require(type(state.get('receipts')) is list)
    scopes = set()
    for receipt in state['receipts']:
        require(type(receipt) is dict)
        require(type(receipt.get('user_id')) is str and receipt['user_id'] in state['users'])
        require(receipt.get('method') == 'POST' and receipt.get('path') in ('/reservations', '/reservation-moves'))
        require(type(receipt.get('key')) is str and 1 <= len(receipt['key']) <= 255)
        scope = (receipt['user_id'], receipt['method'], receipt['path'], receipt['key'])
        require(scope not in scopes)
        scopes.add(scope)
        require(type(receipt.get('body')) is dict and type(receipt.get('response')) is dict)
        response = receipt['response']
        if receipt['path'] == '/reservation-moves':
            require(type(response.get('reservations')) is list and 1 <= len(response['reservations']) <= 8)
            records = response['reservations']
            moves = receipt['body'].get('moves')
            require(type(moves) is list and len(moves) == len(records))
        else:
            records = [response]
        refs = set()
        for index, public_record in enumerate(records):
            require(type(public_record) is dict)
            require('user_id' not in public_record and public_record.get('status') == 'confirmed')
            record = dict(public_record, user_id=receipt['user_id'])
            validate_record(record, state, owner=receipt['user_id'])
            ref = record['reference']
            require(ref in state['reservations'] and ref not in refs)
            refs.add(ref)
            current = state['reservations'][ref]
            for name in ('reservation_id', 'restaurant_id', 'user_id', 'created_at'):
                require(record[name] == current[name])
            if receipt['path'] == '/reservations':
                expected = candidate(state, receipt['body'])
            else:
                move = moves[index]
                require(type(move) is dict and move.get('reference') == ref)
                expected = candidate(state, move, record)
            from .reservations import table_ids
            require(table_ids(expected) == table_ids(record))
            for name in ('restaurant_id', 'party_size', 'starts_at_local'):
                require(expected[name] == record[name])
    return state


def from_fixture(fixture):
    from .reservations import candidate, now
    require(type(fixture) is dict)
    state = empty()
    users, restaurants, bookings = (fixture.get(k) for k in ('users', 'restaurants', 'reservations'))
    require(type(users) is list and type(restaurants) is list and type(bookings) is list)
    validate_restaurants(restaurants)
    # Preserve only the stage-1 contract, not unknown future-stage fields.
    for restaurant in restaurants:
        copied = {k: deepcopy(restaurant[k]) for k in ('id', 'name', 'timezone', 'slot_minutes', 'reservation_duration_minutes', 'cancellation_cutoff_minutes', 'opening_hours', 'tables')}
        copied['opening_hours'] = [{k: h[k] for k in ('weekday', 'opens', 'closes')} for h in copied['opening_hours']]
        copied['tables'] = [{k: t[k] for k in ('id', 'label', 'capacity')} for t in copied['tables']]
        copied['combinable'] = deepcopy(restaurant.get('combinable', []))
        state['restaurants'].append(copied)
    for user in users:
        require(type(user) is dict and ident(user.get('id')) and user['id'] not in state['users'])
        require(type(user.get('password')) is str)
        state['users'][user['id']] = {'id': user['id'], 'email': user.get('email'),
            'display_name': user.get('display_name'), 'password_hash': hash_password(user['password'])}
    for booking in bookings:
        require(type(booking) is dict)
        record = candidate(state, booking)
        record.update(reservation_id=booking.get('id'), reference=booking.get('reference'),
                      user_id=booking.get('user_id'), status=booking.get('status', 'confirmed'), created_at=now().isoformat())
        require(type(record['reference']) is str and record['reference'] not in state['reservations'])
        state['reservations'][record['reference']] = record
    return validate_state(state)


def import_envelope(envelope):
    require(envelope.get('track') == 'tablekeeper' and type(envelope.get('format_version')) is int and envelope['format_version'] == 1)
    try:
        state = deepcopy(envelope.get('state'))
        require(type(state) is dict and type(state.get('schema')) is int)
        if state['schema'] == 1:
            # Upgrade only live record shape. Never rewrite original retry receipts.
            require(type(state.get('restaurants')) is list and type(state.get('reservations')) is dict)
            for restaurant in state['restaurants']:
                require(type(restaurant) is dict)
                restaurant.setdefault('combinable', [])
            for record in state['reservations'].values():
                require(type(record) is dict)
                require('table_ids' not in record)
                record['table_ids'] = [record['table_id']]
            state['schema'] = 2
        return validate_state(state)
    except (APIError, KeyError, TypeError, ValueError, OverflowError):
        invalid('Invalid imported state')


class Store:
    def __init__(self):
        self.lock = RLock()
        self.data = empty()

    def export(self):
        return {'track': 'tablekeeper', 'format_version': 1, 'state': deepcopy(self.data)}
