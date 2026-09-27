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
