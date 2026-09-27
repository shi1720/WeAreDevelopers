"""Portable, validated state and atomic snapshot replacement."""
from copy import deepcopy
from datetime import datetime, timezone
import re
from threading import RLock
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .auth import hash_password, valid_hash
from .validation import APIError, invalid, calendar_date, canonical
from . import policies, history


def empty():
    return {'schema': 4, 'users': {}, 'tokens': {}, 'restaurants': [], 'reservations': {}, 'receipts': [],
            'policies': {}, 'histories': {}, 'series': {}, 'restaurant_revisions': {}, 'plans': {}, 'closures': [], 'series_operations': []}


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
        managers = restaurant.get('manager_user_ids', [])
        require(type(managers) is list and all(ident(uid) for uid in managers) and len(set(managers)) == len(managers))


def selection_body(record):
    """Records expose a singleton alias; request bodies may not send both."""
    body = deepcopy(record)
    if 'table_ids' in body:
        body.pop('table_id', None)
    return body


def validate_terms(terms, state, restaurant):
    require(type(terms) is dict and integer(terms.get('policy_version')))
    version = terms['policy_version']
    for name in ('slot_minutes', 'reservation_duration_minutes'):
        require(integer(terms.get(name), 1))
    require(integer(terms.get('cancellation_cutoff_minutes')))
    require(type(terms.get('capacities')) is dict and all(integer(v, 1) for v in terms['capacities'].values()))
    published = state['policies'][restaurant['id']]
    require(version <= len(published))
    expected = policies.base_terms(restaurant) if version == 0 else {k: v for k, v in published[version - 1].items() if k != 'effective_from'}
    require(terms == expected)


def record_terms(record, state):
    from .reservations import restaurant_for
    restaurant = restaurant_for(state, record['restaurant_id'])
    return record.get('accepted_terms', policies.base_terms(restaurant))


def validate_record(record, state, *, owner=None):
    from .reservations import candidate, restaurant_for
    require(type(record) is dict)
    for name in ('reservation_id', 'reference', 'restaurant_id', 'user_id'):
        require(ident(record.get(name)))
    require(re.fullmatch('[A-Z0-9]{6,12}', record['reference']) is not None)
    require(record['user_id'] in state['users'])
    if owner is not None:
        require(record['user_id'] == owner)
    require(record.get('status') in ('confirmed', 'cancelled'))
    instant(record.get('created_at'))
    terms = record_terms(record, state)
    validate_terms(terms, state, restaurant_for(state, record['restaurant_id']))
    if 'revision' in record or 'accepted_terms' in record:
        require(integer(record.get('revision'), 1) and 'accepted_terms' in record)
    expected = candidate(state, selection_body(record), terms=terms)
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
    require(type(state) is dict and type(state.get('schema')) is int and state['schema'] == 4)
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
    rids = {r['id'] for r in state['restaurants']}
    require(type(state.get('policies')) is dict and set(state['policies']) == rids)
    require(type(state.get('restaurant_revisions')) is dict and set(state['restaurant_revisions']) == rids)
    for restaurant in state['restaurants']:
        rid = restaurant['id']
        require(all(uid in state['users'] for uid in restaurant.get('manager_user_ids', [])))
        require(integer(state['restaurant_revisions'][rid]))
        require(type(state['policies'][rid]) is list)
        for version, policy in enumerate(state['policies'][rid], 1):
            clean = policies.validate_policy(restaurant, policy)
            require(type(policy.get('policy_version')) is int and policy['policy_version'] == version)
            require(policy == dict(clean, policy_version=version))
    require(type(state.get('reservations')) is dict)
    reservation_ids = set()
    for ref, record in state['reservations'].items():
        validate_record(record, state)
        require('table_ids' in record and 'accepted_terms' in record and integer(record.get('revision'), 1))
        require(record['reference'] == ref and record['reservation_id'] not in reservation_ids)
        reservation_ids.add(record['reservation_id'])
    confirmed = [r for r in state['reservations'].values() if r['status'] == 'confirmed']
    check_occupancy(state, confirmed, state['reservations'])
    require(type(state.get('plans')) is dict and type(state.get('closures')) is list and type(state.get('series_operations')) is list)
    validate_histories(state)
    validate_series(state)
    require(type(state.get('receipts')) is list)
    scopes = set()
    adopted_series = set()
    from .portability import validate_operations, validate_plans, validate_stage4_receipt
    collective = validate_operations(state)
    validate_plans(state)
    for receipt in state['receipts']:
        require(type(receipt) is dict)
        require(type(receipt.get('user_id')) is str and receipt['user_id'] in state['users'])
        require(receipt.get('method') == 'POST' and type(receipt.get('path')) is str)
        require(type(receipt.get('key')) is str and 1 <= len(receipt['key']) <= 255)
        scope = (receipt['user_id'], receipt['method'], receipt['path'], receipt['key'])
        require(scope not in scopes)
        scopes.add(scope)
        require(type(receipt.get('body')) is dict and type(receipt.get('response')) is dict)
        response = receipt['response']
        if validate_stage4_receipt(state, receipt):
            continue
        if receipt['path'].startswith('/restaurants/') and receipt['path'].endswith('/policies'):
            from urllib.parse import unquote
            from .reservations import restaurant_for
            match = re.fullmatch('/restaurants/([^/]+)/policies', receipt['path'])
            require(match is not None)
            restaurant = restaurant_for(state, unquote(match[1]))
            require(receipt['user_id'] in restaurant.get('manager_user_ids', []))
            clean = policies.validate_policy(restaurant, receipt['body'])
            version = response.get('policy_version')
            require(integer(version, 1) and version <= len(state['policies'][restaurant['id']]))
            require(response == dict(clean, policy_version=version) == state['policies'][restaurant['id']][version - 1])
            continue
        if receipt['path'] == '/series':
            validate_series_receipt(state, receipt, collective)
            sid = response['series_id']
            require(sid not in adopted_series)
            adopted_series.add(sid)
            continue
        require(receipt['path'] in ('/reservations', '/reservation-moves'))
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
            validate_historical_response(state, record)
            if receipt['path'] == '/reservations':
                expected = candidate(state, receipt['body'], terms=record_terms(record, state))
            else:
                move = moves[index]
                require(type(move) is dict and move.get('reference') == ref)
                expected = candidate(state, move, record, terms=record_terms(record, state))
            from .reservations import table_ids
            require(table_ids(expected) == table_ids(record))
            for name in ('restaurant_id', 'party_size', 'starts_at_local'):
                require(expected[name] == record[name])
    require(adopted_series == set(state['series']))
    return state


def validate_histories(state):
    from .reservations import candidate
    require(type(state.get('histories')) is dict and set(state['histories']) == set(state['reservations']))
    for ref, entries in state['histories'].items():
        current = state['reservations'][ref]
        require(type(entries) is list and len(entries) > 0)
        previous = None
        previous_at = None
        cancelled = False
        for seq, entry in enumerate(entries, 1):
            require(type(entry) is dict and type(entry.get('seq')) is int and entry['seq'] == seq)
            require(type(entry.get('revision')) is int and entry['revision'] == seq)
            at = instant(entry.get('at'))
            require(previous_at is None or at >= previous_at)
            previous_at = at
            event = entry.get('event')
            require(not cancelled and (event == 'created' if seq == 1 else event in ('changed', 'cancelled', 'reassigned')))
            changes = entry.get('changes')
            require(type(changes) is list)
            terms = entry.get('accepted_terms')
            require(type(terms) is dict)
            if seq == 1:
                require(at == instant(current['created_at']))
            if event == 'cancelled':
                require(changes == [] and terms == previous['accepted_terms'])
                resulting = deepcopy(previous)
                resulting['status'] = 'cancelled'
                cancelled = True
            else:
                require(len(changes) > 0)
                body = selection_body(previous) if previous else {'restaurant_id': current['restaurant_id']}
                for change in changes:
                    require(type(change) is dict and set(change) == {'field', 'from', 'to'})
                    name = change['field']
                    require(name in ('table_id', 'table_ids', 'starts_at_local', 'party_size'))
                    if name in ('table_id', 'table_ids'):
                        body.pop('table_id', None)
                        body.pop('table_ids', None)
                    body[name] = deepcopy(change['to'])
                if event == 'reassigned':
                    require(terms == previous['accepted_terms'])
                    resulting = deepcopy(previous)
                    from .reservations import restaurant_for, selection
                    ids, _ = selection(restaurant_for(state, current['restaurant_id']), body)
                    require(sum(terms['capacities'][tid] for tid in ids) >= previous['party_size'])
                    resulting['table_ids'] = ids
                    resulting.pop('table_id', None)
                    if len(ids) == 1:
                        resulting['table_id'] = ids[0]
                    require(changes == [{'field': 'table_ids', 'from': previous['table_ids'], 'to': ids}])
                    require(previous['table_ids'] != ids and ident(entry.get('plan_id')))
                else:
                    resulting = candidate(state, body, terms=terms)
                resulting.update({k: current[k] for k in ('reference', 'reservation_id', 'user_id', 'created_at')})
                resulting['status'] = 'confirmed'
                resulting['revision'] = seq
                if event != 'reassigned':
                    require(canonical(changes) == canonical(history.changes(previous, resulting)))
                validate_record(resulting, state)
            resulting['revision'] = seq
            previous = resulting
        require(current['revision'] == len(entries))
        for name in ('table_ids', 'party_size', 'starts_at_local', 'starts_at', 'ends_at', 'accepted_terms'):
            require(previous[name] == current[name])
        # A fixture/import can start with a cancelled record and no pre-upgrade history.
        require(previous['status'] == current['status'] or (len(entries) == 1 and current['status'] == 'cancelled'))


def validate_historical_response(state, record):
    """A native receipt must name an actual immutable reservation revision."""
    if 'revision' not in record:
        return  # Original stage-1/2 receipts predate histories.
    entries = state['histories'][record['reference']]
    revision = record['revision']
    require(integer(revision, 1) and revision <= len(entries))
    fields = {}
    status = 'confirmed'
    for entry in entries[:revision]:
        if entry['event'] == 'cancelled':
            status = 'cancelled'
        for change in entry['changes']:
            if change['field'] == 'table_id':
                fields['table_ids'] = [change['to']]
            else:
                fields[change['field']] = change['to']
    from .reservations import table_ids
    require(table_ids(record) == fields['table_ids'])
    require(record['starts_at_local'] == fields['starts_at_local'] and record['party_size'] == fields['party_size'])
    require(record['status'] == status and record['accepted_terms'] == entries[revision - 1]['accepted_terms'])


def validate_series(state):
    from datetime import timedelta
    require(type(state.get('series')) is dict)
    members = set()
    rids = {r['id'] for r in state['restaurants']}
    for sid, agreement in state['series'].items():
        require(ident(sid) and type(agreement) is dict and agreement.get('series_id') == sid)
        require(integer(agreement.get('revision'), 1))
        require(type(agreement.get('user_id')) is str and agreement['user_id'] in state['users'])
        require(type(agreement.get('restaurant_id')) is str and agreement['restaurant_id'] in rids)
        interval = agreement.get('interval_weeks')
        require(type(interval) is int and 1 <= interval <= 4)
        occurrences = agreement.get('occurrences')
        require(type(occurrences) is list and 2 <= len(occurrences) <= 12)
        first_date = None
        for index, occurrence in enumerate(occurrences):
            require(type(occurrence) is dict and type(occurrence.get('index')) is int and occurrence['index'] == index)
            require(type(occurrence.get('exception')) is bool)
            ref = occurrence.get('reference')
            require(type(ref) is str and ref in state['reservations'] and ref not in members)
            members.add(ref)
            booking = state['reservations'][ref]
            require(booking['user_id'] == agreement['user_id'] and booking['restaurant_id'] == agreement['restaurant_id'])
            date = calendar_date(occurrence.get('scheduled_date'))
            if first_date is None:
                first_date = date
            require(date == first_date + timedelta(weeks=index * interval))
            if not occurrence['exception']:
                require(booking['starts_at_local'][:10] == date.isoformat())


def validate_series_receipt(state, receipt, collective):
    response, body = receipt['response'], receipt['body']
    sid = response.get('series_id')
    require(type(sid) is str and sid in state['series'])
    agreement = state['series'][sid]
    require(agreement['user_id'] == receipt['user_id'])
    require(type(response.get('revision')) is int and response['revision'] == 1)
    require(type(body.get('count')) is int and body['count'] == len(agreement['occurrences']))
    require(type(body.get('interval_weeks')) is int and body['interval_weeks'] == agreement['interval_weeks'])
    require(type(response.get('interval_weeks')) is int and response['interval_weeks'] == agreement['interval_weeks'])
    require(body.get('anchor_reference') == agreement['occurrences'][0]['reference'])
    occurrences = response.get('occurrences')
    require(type(occurrences) is list and len(occurrences) == len(agreement['occurrences']))
    for index, occurrence in enumerate(occurrences):
        require(type(occurrence) is dict and type(occurrence.get('index')) is int and occurrence['index'] == index)
        require(occurrence.get('exception') is False and occurrence.get('reference') == agreement['occurrences'][index]['reference'])
        public = occurrence.get('reservation')
        require(type(public) is dict and 'user_id' not in public and public.get('status') == 'confirmed')
        record = dict(public, user_id=receipt['user_id'])
        validate_record(record, state)
        ref = occurrence['reference']
        require(record['reference'] == ref and record['starts_at_local'][:10] == agreement['occurrences'][index]['scheduled_date'])
        for name in ('reservation_id', 'restaurant_id', 'user_id', 'created_at'):
            require(record[name] == state['reservations'][ref][name])
        validate_historical_response(state, record)
        # The immutable adoption receipt is the boundary: an anchor may have
        # changed before adoption without becoming a diner exception. Every
        # later real amendment (including one subsequently reverted) is permanent.
        revision = record.get('revision')
        require(integer(revision, 1))
        amended = any(entry['event'] == 'changed'
                      for entry in state['histories'][ref][revision:]
                      if (ref, entry['revision']) not in collective)
        require(agreement['occurrences'][index]['exception'] == amended)


def from_fixture(fixture):
    from .reservations import candidate, now
    require(type(fixture) is dict)
    state = empty()
    users, restaurants, bookings = (fixture.get(k) for k in ('users', 'restaurants', 'reservations'))
    require(type(users) is list and type(restaurants) is list and type(bookings) is list)
    validate_restaurants(restaurants)
    # Preserve only implemented fixture fields, ignoring unknown future fields.
    for restaurant in restaurants:
        copied = {k: deepcopy(restaurant[k]) for k in ('id', 'name', 'timezone', 'slot_minutes', 'reservation_duration_minutes', 'cancellation_cutoff_minutes', 'opening_hours', 'tables')}
        copied['opening_hours'] = [{k: h[k] for k in ('weekday', 'opens', 'closes')} for h in copied['opening_hours']]
        copied['tables'] = [{k: t[k] for k in ('id', 'label', 'capacity')} for t in copied['tables']]
        copied['combinable'] = deepcopy(restaurant.get('combinable', []))
        copied['manager_user_ids'] = deepcopy(restaurant.get('manager_user_ids', []))
        state['restaurants'].append(copied)
        state['policies'][copied['id']] = []
        state['restaurant_revisions'][copied['id']] = 0
    for user in users:
        require(type(user) is dict and ident(user.get('id')) and user['id'] not in state['users'])
        require(type(user.get('password')) is str)
        state['users'][user['id']] = {'id': user['id'], 'email': user.get('email'),
            'display_name': user.get('display_name'), 'password_hash': hash_password(user['password'])}
    for booking in bookings:
        require(type(booking) is dict)
        record = candidate(state, booking)
        record.update(reservation_id=booking.get('id'), reference=booking.get('reference'),
                      user_id=booking.get('user_id'), status=booking.get('status', 'confirmed'), created_at=now().isoformat(), revision=1)
        require(type(record['reference']) is str and record['reference'] not in state['reservations'])
        state['reservations'][record['reference']] = record
        history.initialize(state, record)
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
        if state['schema'] == 2:
            require(type(state.get('restaurants')) is list and type(state.get('reservations')) is dict)
            state.update(policies={}, restaurant_revisions={}, histories={}, series={})
            for restaurant in state['restaurants']:
                require(type(restaurant) is dict)
                restaurant.setdefault('manager_user_ids', [])
                state['policies'][restaurant['id']] = []
                state['restaurant_revisions'][restaurant['id']] = 0
            for record in state['reservations'].values():
                require(type(record) is dict)
                from .reservations import restaurant_for
                record['accepted_terms'] = policies.base_terms(restaurant_for(state, record['restaurant_id']))
                record['revision'] = 1
                history.initialize(state, record)
            state['schema'] = 3
        if state['schema'] == 3:
            state.update(schema=4, plans={}, closures=[], series_operations=[])
        return validate_state(state)
    except (APIError, KeyError, TypeError, ValueError, OverflowError):
        invalid('Invalid imported state')


class Store:
    def __init__(self):
        self.lock = RLock()
        self.data = empty()

    def export(self):
        return {'track': 'tablekeeper', 'format_version': 1, 'state': deepcopy(self.data)}
